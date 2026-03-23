"""
MATHAN AI HEMAN — High Efficiency Market Adaptive Network
CCS is BODY | AI Brain is SOUL | Live Data is BLOOD
"""
import os,json,time,threading,datetime,socket,requests,sqlite3,logging
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from flask import Flask,Response,jsonify,request
from flask_sock import Sock

logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s")
log=logging.getLogger("HEMAN")
PORT=int(os.environ.get("PORT",8000))
DB="/tmp/heman.db"
SCRIP_CACHE="/tmp/heman_scrip.json"
SCRIP_URL="https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
INDEX_CFG={
    "NIFTY":{"step":50,"lot":75,"token":"26000","exchange":"NSE","nfo_name":"NIFTY"},
    "SENSEX":{"step":100,"lot":20,"token":"99926000","exchange":"BSE","nfo_name":"SENSEX"},
}
ANGEL={"api_key":"","client_id":"","pin":"","totp_secret":"","connected":False,
       "jwt_token":"","feed_token":"","session_obj":None,"ws":None,
       "ws_running":False,"ws_thread":None,"error":None,"last_login":None}
SYS={"source":"NONE","index":"NIFTY","auto":True,"fetching":False,"last_fetch":None,
     "error":None,"count":0,"auth_failures":0,"poll_interval":10}
M={"spot":None,"prev":None,"gap":None,"vix":None,"gift":None,"gift_diff":None,
   "atm":None,"pcr":None,"call_oi":None,"put_oi":None,"ce_prem":None,"pe_prem":None,
   "ce_prev":None,"pe_prev":None,"support":None,"resistance":None,"sup_oi":None,
   "res_oi":None,"exp_days":None,"fetch_time":None,"source":None}
OC_DATA={};OC_LOCK=threading.Lock();state_lock=threading.Lock()
_cl_lock=threading.Lock();_clients=[]
AGENTS={
    "l1":{"name":"OI Analyst","signal":None,"detail":"","confidence":0,"weight":1.5,"ts":None},
    "l2":{"name":"Price Action","signal":None,"detail":"","confidence":0,"weight":1.5,"ts":None},
    "l3":{"name":"VIX Monitor","signal":None,"detail":"","confidence":0,"weight":1.5,"ts":None},
    "l4":{"name":"GIFT Tracker","signal":None,"detail":"","confidence":0,"weight":1.0,"ts":None},
    "l5":{"name":"CE Premium","signal":None,"detail":"","confidence":0,"weight":1.0,"ts":None},
    "l6":{"name":"PE Premium","signal":None,"detail":"","confidence":0,"weight":1.0,"ts":None},
    "l7":{"name":"Session Clock","signal":None,"detail":"","confidence":0,"weight":0.8,"ts":None},
    "l8":{"name":"Expiry Watcher","signal":None,"detail":"","confidence":0,"weight":0.8,"ts":None},
    "l9":{"name":"Gap Detector","signal":None,"detail":"","confidence":0,"weight":1.0,"ts":None},
    "l10":{"name":"PCR Engine","signal":None,"detail":"","confidence":0,"weight":1.2,"ts":None},
    "l11":{"name":"Trap Detector","signal":None,"detail":"","confidence":0,"weight":1.5,"ts":None},
    "l12":{"name":"Risk Control","signal":None,"detail":"","confidence":0,"weight":1.2,"ts":None},
    "l13":{"name":"Behaviour AI","signal":None,"detail":"","confidence":0,"weight":2.0,"ts":None},
}
NAMBI={"signal":"WAIT","bull_pct":50,"bear_pct":50,"confidence":"LOW","reasons":[],
       "source":"NONE","computed_at":None,"trap_detected":False,"conflict":False}
L15={"verdict":None,"reason":"","confidence":0,"ts":None}
L16={"trap_status":None,"fake_side":None,"action":None,"confidence":0,"reason":"","ts":None}
L17={"total_trades":0,"wins":0,"losses":0,"win_rate":0.0,"last_updated":None}
EXEC={"active":False,"position":None,"entry_price":None,"stop_loss":None,
      "target":None,"pnl":0,"trade_count_today":0,"daily_loss":0,"capital":10000}
TELEGRAM={"token":"","chat_id":"","enabled":False}
CCS_LOG=[];CCS_LOCK=threading.Lock()

def ccs_log(etype,src,tgt,msg,data=None):
    e={"ts":ist(),"type":etype,"source":src,"target":tgt,"message":msg,"data":data or {}}
    with CCS_LOCK:
        CCS_LOG.append(e)
        if len(CCS_LOG)>120:CCS_LOG.pop(0)
    broadcast({"type":"ccs_event","event":e})

def cl_add(ws):
    with _cl_lock:_clients.append(ws)
def cl_rm(ws):
    with _cl_lock:
        try:_clients.remove(ws)
        except:pass
def cl_snap():
    with _cl_lock:return list(_clients)
def broadcast(p):
    d=json.dumps(p)
    for c in cl_snap():
        try:c.send(d)
        except:cl_rm(c)
def send1(ws,p):
    try:ws.send(json.dumps(p));return True
    except:return False

def db_init():
    c=sqlite3.connect(DB)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal TEXT,entry REAL,exit_p REAL,pnl REAL,result TEXT,reason TEXT,ts TEXT);
        CREATE TABLE IF NOT EXISTS agent_weights(agent_id TEXT PRIMARY KEY,weight REAL);
    """)
    c.commit();c.close()
def db_set(k,v):
    try:
        c=sqlite3.connect(DB)
        c.execute("INSERT OR REPLACE INTO config VALUES(?,?)",(k,str(v)))
        c.commit();c.close()
    except:pass
def db_get(k):
    try:
        c=sqlite3.connect(DB)
        r=c.execute("SELECT value FROM config WHERE key=?",(k,)).fetchone()
        c.close();return r[0] if r else None
    except:return None
def db_load():
    for f in ["api_key","client_id","pin","totp_secret"]:
        v=db_get(f"angel_{f}")
        if v:ANGEL[f]=v
    idx=db_get("index")
    if idx in INDEX_CFG:SYS["index"]=idx
    tt=db_get("tg_token");tc=db_get("tg_chat")
    if tt:TELEGRAM["token"]=tt
    if tc:TELEGRAM["chat_id"]=tc
    if tt and tc:TELEGRAM["enabled"]=True
    cap=db_get("capital")
    if cap:
        try:EXEC["capital"]=float(cap)
        except:pass
def l17_load():
    try:
        c=sqlite3.connect(DB)
        rows=c.execute("SELECT agent_id,weight FROM agent_weights").fetchall()
        c.close()
        for aid,w in rows:
            if aid in AGENTS:AGENTS[aid]["weight"]=float(w)
    except:pass

def ist():
    tz=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
    return datetime.datetime.now(tz).strftime("%H:%M:%S")
def ist_mins():
    tz=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
    t=datetime.datetime.now(tz);return t.hour*60+t.minute
def calc_expiry():
    tz=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
    t=datetime.datetime.now(tz);d2t=(3-t.weekday())%7
    if d2t==0 and t.hour>=15 and t.minute>=30:d2t=7
    return d2t
def local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80));ip=s.getsockname()[0];s.close();return ip
    except:return "127.0.0.1"
def fmt_oi(n):
    if not n:return "—"
    if n>10000000:return f"{n/10000000:.1f}Cr"
    if n>100000:return f"{n/100000:.1f}L"
    if n>1000:return f"{n/1000:.1f}K"
    return str(n)

def load_scrip():
    if os.path.exists(SCRIP_CACHE):
        age=time.time()-os.path.getmtime(SCRIP_CACHE)
        if age<8*3600:
            try:
                with open(SCRIP_CACHE) as f:data=json.load(f)
                log.info(f"[SCRIP] Cache:{len(data)}");return data
            except:pass
    try:
        log.info("[SCRIP] Downloading...")
        r=requests.get(SCRIP_URL,timeout=30);data=r.json()
        with open(SCRIP_CACHE,"w") as f:json.dump(data,f)
        log.info(f"[SCRIP] {len(data)} instruments");return data
    except Exception as e:log.error(f"[SCRIP ERR]{e}");return []

def find_tokens(scrip,index,spot,num=7):
    cfg=INDEX_CFG[index];step=cfg["step"];atm=round(spot/step)*step
    opts=[i for i in scrip if i.get("exch_seg")=="NFO" and i.get("name")==cfg["nfo_name"]
          and i.get("instrumenttype") in ("OPTIDX","OPTSTK")]
    if not opts:return {}
    today=datetime.date.today();expiries=set()
    for o in opts:
        try:
            exp=datetime.datetime.strptime(o.get("expiry",""),"%d%b%Y").date()
            if exp>=today:expiries.add(exp)
        except:pass
    if not expiries:return {}
    nearest=min(expiries);exp_str=nearest.strftime("%d%b%Y").upper()
    log.info(f"[SCRIP] Expiry:{exp_str} ATM:{atm}")
    strikes=set(range(atm-step*num,atm+step*(num+1),step));tokens={}
    for o in opts:
        try:
            if o.get("expiry","")!=exp_str:continue
            sym=o.get("symbol","");ot=sym[-2:]
            if ot not in ("CE","PE"):continue
            strike=float(o.get("strike",0))/100
            if strike not in strikes:continue
            tok=o.get("token","")
            if tok:tokens[tok]={"strike":strike,"type":ot,"symbol":sym}
        except:pass
    log.info(f"[SCRIP] {len(tokens)} tokens");return tokens

def angel_login():
    ak=ANGEL["api_key"];ci=ANGEL["client_id"];pin=ANGEL["pin"];ts=ANGEL["totp_secret"]
    if not all([ak,ci,pin,ts]):raise Exception("Missing credentials")
    log.info(f"[ANGEL] Login:{ci}")
    obj=SmartConnect(api_key=ak)
    totp=pyotp.TOTP(ts).now()
    data=obj.generateSession(ci,pin,totp)
    if not data or data.get("status") is False:
        msg=data.get("message","Login failed") if data else "No response"
        raise Exception(f"Angel login failed:{msg}")
    ANGEL["session_obj"]=obj
    ANGEL["jwt_token"]=data["data"]["jwtToken"]
    ANGEL["feed_token"]=obj.getfeedToken()
    ANGEL["connected"]=True;ANGEL["error"]=None;ANGEL["last_login"]=ist()
    log.info("[ANGEL] Login OK");return True

def angel_ws_start(opt_tokens):
    if ANGEL["ws_running"]:return
    tlist=list(opt_tokens.keys())
    idx_tok=INDEX_CFG[SYS["index"]]["token"]
    _toks=opt_tokens
    def on_data(wsapp,message):
        try:
            if not isinstance(message,dict):return
            token=str(message.get("token",""))
            ltp=message.get("last_traded_price",0)
            if ltp:ltp=ltp/100
            oi=message.get("open_interest",0)
            if token==INDEX_CFG[SYS["index"]]["token"]:
                with state_lock:
                    M["spot"]=ltp;M["fetch_time"]=ist();M["source"]="ANGEL ONE"
                    if M["prev"]:M["gap"]=round(ltp-M["prev"],2)
                    cfg=INDEX_CFG[SYS["index"]]
                    M["atm"]=round(ltp/cfg["step"])*cfg["step"]
                return
            if token in _toks:
                with OC_LOCK:
                    OC_DATA[token]={"ltp":ltp,"oi":oi,"type":_toks[token]["type"],"strike":_toks[token]["strike"]}
        except Exception as e:log.error(f"[WS DATA]{e}")
    def on_open(wsapp):
        log.info("[ANGEL WS] Connected")
        ANGEL["ws_running"]=True;ANGEL["error"]=None
        payload=[{"exchangeType":2,"tokens":tlist}]
        if idx_tok:payload.append({"exchangeType":1,"tokens":[idx_tok]})
        wsapp.sws.subscribe("heman_ccs",3,payload)
        broadcast({"type":"angel_ws_connected","ts":ist()})
        ccs_log("DATA_CONNECTED","ANGEL_ONE","CCS","Angel One WebSocket live")
    def on_error(wsapp,error):
        log.error(f"[ANGEL WS ERR]{error}")
        ANGEL["ws_running"]=False;ANGEL["error"]=str(error)
        broadcast({"type":"angel_ws_error","error":str(error),"ts":ist()})
    def on_close(wsapp):
        log.info("[ANGEL WS] Closed — reconnect 5s")
        ANGEL["ws_running"]=False
        threading.Timer(5,lambda:angel_ws_start(_toks)).start()
    sws=SmartWebSocketV2(ANGEL["jwt_token"],ANGEL["api_key"],ANGEL["client_id"],ANGEL["feed_token"],max_retry_attempt=5)
    sws.on_open=on_open;sws.on_data=on_data;sws.on_error=on_error;sws.on_close=on_close
    ANGEL["ws"]=sws
    def run():
        try:sws.connect()
        except Exception as e:log.error(f"[WS RUN]{e}");ANGEL["ws_running"]=False
    t=threading.Thread(target=run,daemon=True);t.start();ANGEL["ws_thread"]=t

def aggregate_oi():
    with OC_LOCK:snap=dict(OC_DATA)
    if not snap:return
    with state_lock:atm=M["atm"]
    if not atm:return
    tce=tpe=0;ace=ape=None;mce=mpe=0;ss=rs=so=ro=0
    for tok,d in snap.items():
        oi=d.get("oi") or 0;ltp=d.get("ltp") or 0;typ=d.get("type");st=d.get("strike",0)
        if typ=="CE":
            tce+=oi
            if oi>mce:mce=oi;rs=st;ro=oi
            if st==atm:ace=ltp
        elif typ=="PE":
            tpe+=oi
            if oi>mpe:mpe=oi;ss=st;so=oi
            if st==atm:ape=ltp
    pcr=round(tpe/tce,2) if tce>0 else None
    with state_lock:
        M["ce_prev"]=M["ce_prem"];M["pe_prev"]=M["pe_prem"]
        M["call_oi"]=tce;M["put_oi"]=tpe;M["pcr"]=pcr
        M["ce_prem"]=ace;M["pe_prem"]=ape
        M["support"]=ss or None;M["resistance"]=rs or None
        M["sup_oi"]=so or None;M["res_oi"]=ro or None
        M["source"]="ANGEL ONE";M["fetch_time"]=ist();M["exp_days"]=calc_expiry()

def tg_alert(msg):
    if not TELEGRAM["enabled"]:return
    try:
        url=f"https://api.telegram.org/bot{TELEGRAM['token']}/sendMessage"
        requests.post(url,json={"chat_id":TELEGRAM["chat_id"],"text":msg},timeout=5)
    except Exception as e:log.error(f"[TG]{e}")

def compute_agent(aid):
    with state_lock:
        spot=M["spot"];atm=M["atm"];pcr=M["pcr"];vix=M["vix"];gd=M["gift_diff"]
        ce=M["ce_prem"];pe=M["pe_prem"];cep=M["ce_prev"];pep=M["pe_prev"]
        sup=M["support"];res=M["resistance"];exp=M["exp_days"];gap=M["gap"]
    mins=ist_mins();sig="hold";det="";conf=50
    if aid=="l1":
        if pcr is not None:
            if pcr>1.5:sig,det,conf="bull",f"PCR {pcr} — Strong Put writing. Bulls control.",90
            elif pcr>1.2:sig,det,conf="bull",f"PCR {pcr} — Moderate bullish.",70
            elif pcr<0.6:sig,det,conf="bear",f"PCR {pcr} — Strong Call writing. Bears control.",90
            elif pcr<0.8:sig,det,conf="bear",f"PCR {pcr} — Bearish OI.",70
            else:sig,det,conf="hold",f"PCR {pcr} — Neutral.",50
        else:sig,det,conf="hold","PCR N/A",0
    elif aid=="l2":
        if res and spot and spot>res:sig,det,conf="bull",f"Above resistance {int(res)} — Breakout!",85
        elif sup and spot and spot<sup:sig,det,conf="bear",f"Below support {int(sup)} — Breakdown!",85
        elif spot and atm and spot>atm+50:sig,det,conf="bull",f"Spot {spot:.0f} above ATM {atm}",65
        elif spot and atm and spot<atm-50:sig,det,conf="bear",f"Spot {spot:.0f} below ATM {atm}",65
        elif spot and atm:sig,det,conf="hold",f"At ATM {atm} — Range",50
        else:sig,det,conf="hold","Spot N/A",0
    elif aid=="l3":
        if vix:
            if vix<12:sig,det,conf="bull",f"VIX {vix:.1f} — Very calm.",85
            elif vix<15:sig,det,conf="bull",f"VIX {vix:.1f} — Calm.",70
            elif vix<18:sig,det,conf="hold",f"VIX {vix:.1f} — Caution.",50
            elif vix<22:sig,det,conf="bear",f"VIX {vix:.1f} — High fear!",75
            else:sig,det,conf="bear",f"VIX {vix:.1f} — EXTREME. Avoid!",95
        else:sig,det,conf="hold","VIX N/A",0
    elif aid=="l4":
        if gd is not None:
            if gd>150:sig,det,conf="bull",f"GIFT +{round(gd)} — Strong gap up",85
            elif gd>60:sig,det,conf="bull",f"GIFT +{round(gd)} — Mild gap up",65
            elif gd<-150:sig,det,conf="bear",f"GIFT {round(gd)} — Strong gap down",85
            elif gd<-60:sig,det,conf="bear",f"GIFT {round(gd)} — Mild gap down",65
            else:sig,det,conf="hold",f"GIFT ±{round(abs(gd))} — Flat",50
        else:sig,det,conf="hold","GIFT N/A",0
    elif aid=="l5":
        if ce is not None:
            chg=(ce-cep) if cep else 0
            if chg>10:sig,det,conf="bull",f"CE ₹{ce:.0f} +{chg:.0f} — Bulls buying CE",75
            elif chg>5:sig,det,conf="bull",f"CE ₹{ce:.0f} +{chg:.0f} — CE rising",60
            elif chg<-10:sig,det,conf="bear",f"CE ₹{ce:.0f} {chg:.0f} — Bulls exiting",75
            elif chg<-5:sig,det,conf="bear",f"CE ₹{ce:.0f} {chg:.0f} — CE falling",60
            else:sig,det,conf="hold",f"CE ₹{ce:.0f} — Stable",50
        else:sig,det,conf="hold","CE N/A",0
    elif aid=="l6":
        if pe is not None:
            chg=(pe-pep) if pep else 0
            if chg>10:sig,det,conf="bear",f"PE ₹{pe:.0f} +{chg:.0f} — Bears buying PE",75
            elif chg>5:sig,det,conf="bear",f"PE ₹{pe:.0f} +{chg:.0f} — PE rising",60
            elif chg<-10:sig,det,conf="bull",f"PE ₹{pe:.0f} {chg:.0f} — Bears exiting",75
            elif chg<-5:sig,det,conf="bull",f"PE ₹{pe:.0f} {chg:.0f} — PE falling",60
            else:sig,det,conf="hold",f"PE ₹{pe:.0f} — Stable",50
        else:sig,det,conf="hold","PE N/A",0
    elif aid=="l7":
        if mins<555:sig,det,conf="hold","Pre-market",0
        elif mins<570:sig,det,conf="hold","Pre-open 9:00-9:15",30
        elif mins<600:sig,det,conf="bull","Open hour — High volatility",70
        elif mins<660:sig,det,conf="bull","9:15-11:00 — Best entry window",80
        elif mins<780:sig,det,conf="hold","11:00-1:00 — Mid session",60
        elif mins<870:sig,det,conf="hold","1:00-2:30 — Afternoon",50
        elif mins<920:sig,det,conf="hold","2:30-3:20 — Expiry window",60
        elif mins<930:sig,det,conf="bear","3:20-3:30 — Last 10min. Risk!",70
        else:sig,det,conf="hold","Post market",0
    elif aid=="l8":
        if exp is not None:
            if exp==0:sig,det,conf="bull","TODAY EXPIRY — Max theta decay",80
            elif exp==1:sig,det,conf="hold","Pre-expiry — Volatile tomorrow",60
            elif exp<=3:sig,det,conf="hold",f"{exp} days — Near expiry",55
            else:sig,det,conf="hold",f"{exp} days to expiry",50
        else:sig,det,conf="hold","Expiry N/A",0
    elif aid=="l9":
        if gap is not None:
            if gap>150:sig,det,conf="bull",f"Strong GAP UP +{round(gap)}",85
            elif gap>60:sig,det,conf="bull",f"Mild GAP UP +{round(gap)}",65
            elif gap<-150:sig,det,conf="bear",f"Strong GAP DOWN {round(gap)}",85
            elif gap<-60:sig,det,conf="bear",f"Mild GAP DOWN {round(gap)}",65
            else:sig,det,conf="hold",f"Flat ±{round(abs(gap))}",50
        else:sig,det,conf="hold","Gap N/A",0
    elif aid=="l10":
        if pcr is not None:
            if pcr>1.5:sig,det,conf="bull",f"PCR {pcr} — Heavy Put OI. Floor strong.",85
            elif pcr>1.2:sig,det,conf="bull",f"PCR {pcr} — Bullish",70
            elif pcr<0.6:sig,det,conf="bear",f"PCR {pcr} — Heavy Call OI. Ceiling strong.",85
            elif pcr<0.8:sig,det,conf="bear",f"PCR {pcr} — Bearish",70
            else:sig,det,conf="hold",f"PCR {pcr} — Neutral",50
        else:sig,det,conf="hold","PCR N/A",0
    elif aid=="l11":
        trap=False;tmsg=""
        if pcr and spot and atm:
            if pcr>1.3 and spot<atm-60:trap=True;tmsg=f"PCR bullish({pcr}) but spot below ATM — BULL TRAP?"
            elif pcr<0.75 and spot>atm+60:trap=True;tmsg=f"PCR bearish({pcr}) but spot above ATM — BEAR TRAP?"
        if vix and vix>20 and pcr and pcr>1.2:trap=True;tmsg=f"VIX {vix:.1f} high + Bullish PCR — Manipulation?"
        if trap:sig,det,conf="hold",f"⚠️ {tmsg}",85
        else:sig,det,conf="hold","No trap detected. Normal behaviour.",40
    elif aid=="l12":
        if vix and vix>22:sig,det,conf="bear",f"VIX {vix:.1f} EXTREME — AVOID ALL TRADES",99
        elif vix and vix>18:sig,det,conf="hold",f"VIX {vix:.1f} HIGH — 1 lot max. Tight SL.",75
        elif EXEC["daily_loss"]<-EXEC["capital"]*0.02:sig,det,conf="bear","Daily loss limit — STOP TRADING",99
        elif EXEC["trade_count_today"]>=5:sig,det,conf="hold","Max 5 trades today.",80
        elif exp==0 and mins>=900:sig,det,conf="hold","Expiry last hour — Theta risk",70
        else:sig,det,conf="bull","Risk OK. Trade allowed.",70
    elif aid=="l13":
        bc=berc=hc=0
        for a,ag in AGENTS.items():
            if a=="l13":continue
            s=ag.get("signal");w=ag.get("weight",1.0);c=ag.get("confidence",50)/100
            if s=="bull":bc+=w*c
            elif s=="bear":berc+=w*c
            else:hc+=w*c
        tot=bc+berc+hc or 1;bp=bc/tot*100;brp=berc/tot*100
        if bp>65:sig,det,conf="bull",f"System Bull: {bp:.0f}% agents bullish",int(bp)
        elif brp>65:sig,det,conf="bear",f"System Bear: {brp:.0f}% agents bearish",int(brp)
        elif abs(bp-brp)<15:sig,det,conf="hold",f"Conflicted: Bull {bp:.0f}% Bear {brp:.0f}% — WAIT",55
        else:
            dom="bull" if bp>brp else "bear"
            sig,det,conf=dom,f"Weak {dom}: {max(bp,brp):.0f}%",int(max(bp,brp))
    with state_lock:
        AGENTS[aid]["signal"]=sig;AGENTS[aid]["detail"]=det
        AGENTS[aid]["confidence"]=conf;AGENTS[aid]["ts"]=ist()
    return {"id":aid,"signal":sig,"detail":det,"confidence":conf}

def compute_all():
    for aid in list(AGENTS.keys()):
        if aid!="l13":compute_agent(aid)
    compute_agent("l13")

def run_l15():
    with state_lock:
        spot=M["spot"];atm=M["atm"];pcr=M["pcr"]
        ce=M["ce_prem"];pe=M["pe_prem"];cep=M["ce_prev"];pep=M["pe_prev"]
        sup=M["support"];res=M["resistance"];vix=M["vix"]
    if not spot or not atm:
        L15.update({"verdict":"IGNORE","reason":"No spot data","confidence":0,"ts":ist()});return
    ok=0;tot=4
    if sup and res and sup<=spot<=res:ok+=1
    if pcr:
        if (pcr>1.2 and spot>atm) or (pcr<0.8 and spot<atm):ok+=1
    if ce and pe and cep and pep:
        if ((ce-cep)>0 and (pe-pep)<0) or ((ce-cep)<0 and (pe-pep)>0):ok+=1
    if vix and vix<20:ok+=1
    r=ok/tot
    if r>=0.75:v,rea,c="TRUE_MOVE",f"{ok}/{tot} checks — Real move",int(r*100)
    elif r>=0.5:v,rea,c="TRAP",f"{ok}/{tot} — Possible trap",int(r*100)
    elif r>=0.25:v,rea,c="FAKE_MOVE",f"{ok}/{tot} — Likely fake",60
    else:v,rea,c="IGNORE","Too many contradictions",70
    L15.update({"verdict":v,"reason":rea,"confidence":c,"ts":ist()})
    ccs_log("L15_RESULT","L15_TRUTH","NAMBI",f"{v}:{rea}")

def run_l16():
    with state_lock:
        pcr=M["pcr"];coi=M["call_oi"];poi=M["put_oi"]
        ce=M["ce_prem"];pe=M["pe_prem"];cep=M["ce_prev"];pep=M["pe_prev"]
    if not all([pcr,coi,poi]):
        L16.update({"trap_status":"NO_DATA","fake_side":None,"action":"NO_TRADE","confidence":0,"reason":"OI not available","ts":ist()});return
    cechg=(ce-cep) if (ce and cep) else 0
    pechg=(pe-pep) if (pe and pep) else 0
    ts=act=fake=rea="";conf=50
    if pcr>1.2 and coi>poi*0.9 and cechg>5:
        ts="CALL_TRAP";fake="CALL";act="BUY_PE";conf=82
        rea=f"PCR bullish({pcr}) BUT Call OI {fmt_oi(coi)} rising — Smart money short CE. Market may fall."
    elif pcr<0.8 and poi>coi*0.9 and pechg>5:
        ts="PUT_TRAP";fake="PUT";act="BUY_CE";conf=82
        rea=f"PCR bearish({pcr}) BUT Put OI {fmt_oi(poi)} rising — Smart money short PE. Market may rise."
    elif pcr>1.2 and poi>coi:
        ts="TRUE_MOVE";act="BUY_CE";conf=75
        rea=f"PCR {pcr} + Put OI {fmt_oi(poi)} > Call OI — True bull move"
    elif pcr<0.8 and coi>poi:
        ts="TRUE_MOVE";act="BUY_PE";conf=75
        rea=f"PCR {pcr} + Call OI {fmt_oi(coi)} > Put OI — True bear move"
    elif abs(coi-poi)<poi*0.1:
        ts="SIDEWAYS";act="NO_TRADE";conf=70
        rea=f"Call OI {fmt_oi(coi)} ≈ Put OI {fmt_oi(poi)} — Sideways. No trade."
    else:
        ts="NEUTRAL";act="NO_TRADE";conf=50
        rea=f"PCR {pcr} — Inconclusive"
    L16.update({"trap_status":ts,"fake_side":fake or None,"action":act,"confidence":conf,"reason":rea,"ts":ist()})
    ccs_log("L16_RESULT","L16_CONTRADICTION","NAMBI",f"{ts}→{act}({conf}%):{rea}")

def run_nambi():
    l12=AGENTS.get("l12",{})
    if l12.get("signal")=="bear" and l12.get("confidence",0)>=99:
        NAMBI.update({"signal":"WAIT","bull_pct":0,"bear_pct":0,"confidence":"BLOCKED",
                      "reasons":[l12.get("detail","Risk block")],"trap_detected":False,
                      "conflict":False,"source":"L12_BLOCK","computed_at":ist()})
        broadcast({"type":"nambi_update","nambi":dict(NAMBI)});return
    bull=bear=0.0;reasons=[];trap=False;conflict=False
    for aid,ag in AGENTS.items():
        s=ag.get("signal");w=ag.get("weight",1.0);c=ag.get("confidence",50)/100;det=ag.get("detail","")
        if s=="bull":bull+=w*c;reasons.append(f"[{ag['name']}] BULL — {det}")
        elif s=="bear":bear+=w*c;reasons.append(f"[{ag['name']}] BEAR — {det}")
    l16a=L16.get("action");l16c=L16.get("confidence",0)/100;l16w=2.5
    if l16a=="BUY_CE":bull+=l16w*l16c;reasons.append(f"[L16] BUY CE — {L16.get('reason','')}")
    elif l16a=="BUY_PE":bear+=l16w*l16c;reasons.append(f"[L16] BUY PE — {L16.get('reason','')}")
    l15v=L15.get("verdict")
    if l15v=="FAKE_MOVE":bull*=0.3;bear*=0.3;trap=True;reasons.append("[L15] FAKE MOVE — Signals dampened")
    elif l15v=="TRAP":bull*=0.5;bear*=0.5;trap=True;reasons.append(f"[L15] TRAP:{L15.get('reason','')}")
    total=bull+bear or 1;bpct=round(bull/total*100);brpct=100-bpct
    if 40<=bpct<=60:conflict=True
    thr=62
    if trap or conflict or l15v in ("FAKE_MOVE","TRAP"):sig="WAIT";cl="LOW"
    elif bpct>=thr:sig="BUY CE";cl="HIGH" if bpct>=75 else "MEDIUM"
    elif brpct>=thr:sig="BUY PE";cl="HIGH" if brpct>=75 else "MEDIUM"
    else:sig="WAIT";cl="LOW"
    NAMBI.update({"signal":sig,"bull_pct":bpct,"bear_pct":brpct,"confidence":cl,
                  "reasons":reasons[-8:],"trap_detected":trap,"conflict":conflict,
                  "source":"L14_NAMBI","computed_at":ist()})
    broadcast({"type":"nambi_update","nambi":dict(NAMBI)})
    ccs_log("NAMBI_DECISION","L14_NAMBI","EXEC",f"{sig}|Bull:{bpct}%Bear:{brpct}%|{cl}")
    if sig in ("BUY CE","BUY PE") and cl in ("HIGH","MEDIUM"):
        price=M.get("ce_prem") if sig=="BUY CE" else M.get("pe_prem")
        msg=f"🔔 HEMAN: {sig}\nConfidence:{cl} | Bull:{bpct}% Bear:{brpct}%\nATM:{M.get('atm','—')}"
        if price:msg+=f" | Premium:₹{price:.0f}"
        tg_alert(msg)

def full_cycle():
    if SYS["fetching"]:return
    SYS["fetching"]=True
    try:
        if ANGEL["connected"] and ANGEL["ws_running"]:aggregate_oi()
        SYS["count"]+=1;SYS["last_fetch"]=ist()
        ccs_log("CYCLE","CCS","ALL",f"Cycle #{SYS['count']}")
        compute_all();run_l16();run_l15();run_nambi()
        broadcast({"type":"full_state","state":build_state()})
    except Exception as e:log.error(f"[CYCLE ERR]{e}")
    finally:SYS["fetching"]=False

def poll_loop():
    while True:
        try:
            if SYS["auto"] and SYS["source"]!="NONE":full_cycle()
        except Exception as e:log.error(f"[POLL]{e}")
        time.sleep(SYS["poll_interval"])

def push_loop():
    while True:
        try:
            broadcast({"type":"heartbeat","ts":ist(),"angel":ANGEL["connected"],
                       "ws":ANGEL["ws_running"],"count":SYS["count"]})
        except:pass
        time.sleep(5)

def do_angel_connect(ak,ci,pin,ts):
    ANGEL["api_key"]=ak;ANGEL["client_id"]=ci;ANGEL["pin"]=pin;ANGEL["totp_secret"]=ts
    for f,v in [("api_key",ak),("client_id",ci),("pin",pin),("totp_secret",ts)]:
        db_set(f"angel_{f}",v)
    broadcast({"type":"status_msg","msg":"Connecting to Angel One...","ts":ist()})
    try:
        angel_login()
        with state_lock:SYS["source"]="ANGEL ONE"
        db_set("source","ANGEL ONE")
        broadcast({"type":"angel_ok","ts":ist(),"client":ci})
        ccs_log("ANGEL_LOGIN","ANGEL_ONE","CCS",f"Login OK:{ci}")
        broadcast({"type":"status_msg","msg":"Loading option chain...","ts":ist()})
        scrip=load_scrip()
        with state_lock:spot=M["spot"]
        if not spot:
            idx=SYS["index"];sym={"NIFTY":"%5ENSEI","SENSEX":"%5EBSESN"}[idx]
            try:
                r=requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                    params={"interval":"1m","range":"1d"},headers={"User-Agent":"Mozilla/5.0"},timeout=10)
                sp=r.json().get("chart",{}).get("result",[{}])[0].get("meta",{}).get("regularMarketPrice",0)
                if sp:
                    cfg=INDEX_CFG[idx]
                    with state_lock:M["spot"]=sp;M["atm"]=round(sp/cfg["step"])*cfg["step"]
                    spot=sp
            except:pass
        if spot:
            toks=find_tokens(scrip,SYS["index"],spot)
            if toks:
                angel_ws_start(toks)
                broadcast({"type":"status_msg","msg":f"WebSocket live — {len(toks)} tokens","ts":ist()})
            else:broadcast({"type":"status_msg","msg":"No option tokens found","ts":ist()})
        else:broadcast({"type":"status_msg","msg":"Spot not available","ts":ist()})
        full_cycle()
    except Exception as e:
        log.error(f"[ANGEL CONNECT ERR]{e}")
        ANGEL["connected"]=False;ANGEL["error"]=str(e);SYS["auth_failures"]+=1
        broadcast({"type":"angel_err","msg":str(e),"ts":ist()})

def build_state():
    with state_lock:m=dict(M);s=dict(SYS)
    return {
        "sys":s,"market":m,
        "agents":{k:{"name":v["name"],"signal":v["signal"],"detail":v["detail"],
                     "confidence":v["confidence"],"weight":v["weight"],"ts":v["ts"]}
                  for k,v in AGENTS.items()},
        "nambi":dict(NAMBI),"l15":dict(L15),"l16":dict(L16),
        "l17":{"total_trades":L17["total_trades"],"wins":L17["wins"],
               "losses":L17["losses"],"win_rate":L17["win_rate"]},
        "angel":{"connected":ANGEL["connected"],"ws_running":ANGEL["ws_running"],
                 "error":ANGEL["error"],"client_id":ANGEL["client_id"],"last_login":ANGEL["last_login"]},
        "telegram":{"enabled":TELEGRAM["enabled"]},"ts":ist(),
    }

app=Flask(__name__)
# ── FLASK APP ─────────────────────────────────────────────────────
app=Flask(__name__)
sock=Sock(app)

# ── REST: ANGEL CONNECT ───────────────────────────────────────────
@app.route("/connect_angel",methods=["POST"])
def connect_angel_rest():
    d=request.get_json(force=True) or {}
    ak=d.get("api_key","").strip();ci=d.get("client_id","").strip()
    pin=d.get("pin","").strip();ts=d.get("totp_secret","").strip()
    if not all([ak,ci,pin,ts]):return jsonify({"ok":False,"error":"All 4 required"}),400
    threading.Thread(target=do_angel_connect,args=(ak,ci,pin,ts),daemon=True).start()
    return jsonify({"ok":True,"msg":"Login started"})

# ── REST: STATE (polling) ─────────────────────────────────────────
@app.route("/api/state")
def api_state():
    return jsonify(build_state())

@app.route("/api/fetch",methods=["POST"])
def api_fetch():
    threading.Thread(target=full_cycle,daemon=True).start()
    return jsonify({"ok":True})

@app.route("/api/set_index",methods=["POST"])
def api_set_index():
    d=request.get_json(force=True) or {}
    idx=d.get("index","NIFTY").upper()
    if idx in INDEX_CFG:
        with state_lock:SYS["index"]=idx
        db_set("index",idx)
    return jsonify({"ok":True,"index":SYS["index"]})

@app.route("/api/set_auto",methods=["POST"])
def api_set_auto():
    d=request.get_json(force=True) or {}
    SYS["auto"]=bool(d.get("on",True))
    return jsonify({"ok":True,"auto":SYS["auto"]})

@app.route("/api/set_telegram",methods=["POST"])
def api_set_telegram():
    d=request.get_json(force=True) or {}
    tt=d.get("token","").strip();tc=d.get("chat_id","").strip()
    if tt and tc:
        TELEGRAM["token"]=tt;TELEGRAM["chat_id"]=tc;TELEGRAM["enabled"]=True
        db_set("tg_token",tt);db_set("tg_chat",tc)
        tg_alert("✅ HEMAN Telegram connected!")
        return jsonify({"ok":True})
    return jsonify({"ok":False}),400

@app.route("/api/set_capital",methods=["POST"])
def api_set_capital():
    d=request.get_json(force=True) or {}
    try:
        EXEC["capital"]=float(d.get("capital",10000))
        db_set("capital",EXEC["capital"])
    except:pass
    return jsonify({"ok":True,"capital":EXEC["capital"]})

@app.route("/api/ccs")
def api_ccs():
    with CCS_LOCK:return jsonify({"events":list(CCS_LOG[-50:])})

# ── SSE: LIVE EVENTS ──────────────────────────────────────────────
@app.route("/api/events")
def api_events():
    def stream():
        last=0
        while True:
            try:
                state=build_state()
                data=json.dumps({"type":"state","state":state,"ts":ist()})
                yield f"data: {data}\n\n"
                time.sleep(3)
            except GeneratorExit:break
            except:time.sleep(5)
    return Response(stream(),mimetype="text/event-stream",
                    headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ── WEBSOCKET (kept for compatibility) ───────────────────────────
@sock.route("/ws")
def ws_handler(ws):
    _clients.append(ws)
    try:
        send1(ws,{"type":"connected","ts":ist()})
        send1(ws,{"type":"full_state","state":build_state()})
        while True:
            raw=ws.receive(timeout=30)
            if raw is None:break
            try:d=json.loads(raw)
            except:continue
            t=d.get("type","")
            if t=="ping":send1(ws,{"type":"pong","ts":ist()})
            elif t=="connect_angel":
                ak=d.get("api_key","").strip();ci=d.get("client_id","").strip()
                pin=d.get("pin","").strip();ts2=d.get("totp_secret","").strip()
                if all([ak,ci,pin,ts2]):
                    threading.Thread(target=do_angel_connect,args=(ak,ci,pin,ts2),daemon=True).start()
            elif t=="set_index":
                idx=d.get("index","NIFTY").upper()
                if idx in INDEX_CFG:
                    with state_lock:SYS["index"]=idx
                    db_set("index",idx)
            elif t=="fetch":threading.Thread(target=full_cycle,daemon=True).start()
            elif t=="set_auto":SYS["auto"]=bool(d.get("on",True))
            elif t=="get_state":send1(ws,{"type":"full_state","state":build_state()})
            elif t=="get_ccs_log":
                with CCS_LOCK:send1(ws,{"type":"ccs_history","events":list(CCS_LOG[-50:])})
    except Exception as e:log.error(f"[WS]{e}")
    finally:
        try:_clients.remove(ws)
        except:pass

@app.route("/ping")
def ping():
    return jsonify({"pong":True,"time":ist(),"angel":ANGEL["connected"],"ws":ANGEL["ws_running"],"system":"MATHAN AI HEMAN"})

@app.route("/status")
def status():return jsonify(build_state())

@app.route("/")
@app.route("/dashboard")
def dashboard():return Response(DASHBOARD_HTML,mimetype="text/html")



DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>MATHAN AI HEMAN</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#060a0e;--bg2:#0c1218;--bg3:#101820;--brd:#1a2835;--gold:#f0a500;--grn:#00e676;--red:#ff1744;--blu:#29b6f6;--pur:#ce93d8;--orn:#ff9800;--txt:#cdd9e5;--dim:#3a5268;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--txt);font-family:Rajdhani,sans-serif;padding-bottom:55px;}
body::before{content:'';position:fixed;inset:0;background:linear-gradient(rgba(240,165,0,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(240,165,0,.018) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.15}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(0,230,118,.4)}70%{box-shadow:0 0 0 8px rgba(0,230,118,0)}}
.hdr{position:sticky;top:0;z-index:100;background:linear-gradient(#080d12,rgba(6,10,14,.97));border-bottom:2px solid var(--gold);padding:10px 14px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 4px 32px rgba(240,165,0,.2);}
.logo{font-family:Orbitron;font-size:12px;font-weight:900;color:var(--gold);letter-spacing:2px;}
.logo small{display:block;font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-top:2px;}
.hclock{font-family:Orbitron;font-size:13px;color:var(--gold);}
.hlive{font-size:9px;font-family:'Share Tech Mono';padding:2px 8px;border-radius:3px;}
.hlive.on{border:1px solid var(--grn);color:var(--grn);}
.hlive.off{border:1px solid var(--red);color:var(--red);}
.sbar{display:flex;justify-content:space-between;padding:4px 12px;background:var(--bg2);border-bottom:1px solid var(--brd);font-family:'Share Tech Mono';font-size:9px;}
.sdot{width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:middle;}
.sdot.ok{background:var(--grn);animation:pulse 2s infinite;}
.sdot.wait{background:var(--gold);animation:blink 1s infinite;}
.main{padding:10px;max-width:480px;margin:0 auto;position:relative;z-index:1;}
.banner{background:linear-gradient(135deg,rgba(240,165,0,.07),rgba(240,165,0,.02));border:1px solid rgba(240,165,0,.3);border-radius:11px;padding:10px 14px;margin-bottom:9px;text-align:center;}
.btitle{font-family:Orbitron;font-size:16px;font-weight:900;color:var(--gold);letter-spacing:3px;}
.bsub{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-top:3px;}
.src-row{display:flex;justify-content:space-between;padding:6px 11px;border-radius:7px;margin-bottom:9px;font-family:'Share Tech Mono';font-size:9px;border:1px solid var(--brd);background:var(--bg2);}
.src-row.live{border-color:rgba(0,230,118,.5);color:var(--grn);}
.src-row.none{border-color:rgba(255,23,68,.25);color:var(--red);}
.card{background:var(--bg2);border:1px solid var(--brd);border-radius:12px;padding:12px;margin-bottom:9px;}
.ctitle{font-family:Orbitron;font-size:9px;color:var(--gold);letter-spacing:1px;margin-bottom:9px;display:flex;justify-content:space-between;align-items:center;}
.badge{display:inline-flex;padding:1px 7px;border-radius:8px;font-family:'Share Tech Mono';font-size:7px;}
.badge.live{background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.3);color:var(--grn);}
.badge.wait{background:rgba(41,182,246,.08);border:1px solid rgba(41,182,246,.2);color:var(--blu);}
.inp{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:6px;color:var(--txt);padding:9px 10px;font-size:14px;font-family:'Share Tech Mono';outline:none;margin-bottom:7px;}
.inp:focus{border-color:var(--orn);}
.lbl{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-bottom:3px;}
.btn{width:100%;padding:12px;border-radius:8px;cursor:pointer;font-family:Orbitron;font-size:10px;font-weight:700;letter-spacing:1px;margin-top:6px;border:none;}
.btn-pur{background:rgba(206,147,216,.15);border:1px solid var(--pur)!important;color:var(--pur);}
.btn-ora{background:rgba(255,152,0,.12);border:1px solid var(--orn)!important;color:var(--orn);}
.btn-grn{background:rgba(0,230,118,.12);border:1px solid var(--grn)!important;color:var(--grn);}
.btn-blu{background:rgba(41,182,246,.1);border:1px solid var(--blu)!important;color:var(--blu);}
.btn:disabled{opacity:.4;cursor:not-allowed;}
.idx-row{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.ib{background:var(--bg3);border:2px solid var(--brd);border-radius:9px;padding:10px;text-align:center;cursor:pointer;}
.ib.on{border-color:var(--gold);}
.ib-name{font-family:Orbitron;font-size:14px;font-weight:900;}
.ib.on .ib-name{color:var(--gold);}
.ib-spot{font-family:'Share Tech Mono';font-size:12px;color:var(--grn);margin-top:3px;}
.ib-atm{font-family:'Share Tech Mono';font-size:8px;color:var(--blu);margin-top:2px;}
.mstrip{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-bottom:9px;}
.mc{background:var(--bg2);border:1px solid var(--brd);border-radius:8px;padding:8px;text-align:center;}
.mc-n{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:3px;}
.mc-v{font-family:Orbitron;font-size:14px;font-weight:700;}
.oi-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.oi-cell{background:var(--bg3);border-radius:7px;padding:9px;text-align:center;border:1px solid var(--brd);}
.oi-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:3px;}
.oi-val{font-family:Orbitron;font-size:15px;font-weight:700;}
.pcr-wrap{background:var(--bg3);border-radius:7px;padding:9px;margin-bottom:7px;}
.pcr-lbl{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-bottom:5px;display:flex;justify-content:space-between;}
.pcr-bg{height:11px;border-radius:5px;background:rgba(255,255,255,.05);overflow:hidden;margin-bottom:4px;}
.pcr-fill{height:100%;border-radius:5px;transition:width .8s;}
.pcr-marks{display:flex;justify-content:space-between;font-family:'Share Tech Mono';font-size:7px;color:var(--dim);}
.sr-row{display:grid;grid-template-columns:1fr 1fr;gap:6px;}
.sr-cell{border-radius:7px;padding:9px;text-align:center;}
.sr-sup{background:rgba(0,230,118,.07);border:1px solid rgba(0,230,118,.2);}
.sr-res{background:rgba(255,23,68,.07);border:1px solid rgba(255,23,68,.2);}
.sr-lbl{font-family:'Share Tech Mono';font-size:7px;margin-bottom:3px;}
.sr-val{font-family:Orbitron;font-size:15px;font-weight:700;}
.prem-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.prem-cell{background:var(--bg3);border-radius:8px;padding:10px;border:2px solid var(--brd);text-align:center;}
.ptype{font-family:Orbitron;font-size:10px;font-weight:700;margin-bottom:4px;}
.pval{font-family:Orbitron;font-size:24px;font-weight:700;}
.pchg{font-family:'Share Tech Mono';font-size:9px;margin-top:3px;}
.ag-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:6px;}
.agc{background:var(--bg3);border:1px solid var(--brd);border-radius:8px;padding:9px;position:relative;overflow:hidden;}
.agc::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--brd);}
.agc.bull::before{background:var(--grn);}
.agc.bear::before{background:var(--red);}
.agc.hold::before{background:var(--gold);}
.ag-top{display:flex;justify-content:space-between;margin-bottom:3px;}
.ag-id{font-family:Orbitron;font-size:7px;color:var(--dim);}
.ag-sig{font-family:'Share Tech Mono';font-size:9px;font-weight:700;}
.ag-sig.bull{color:var(--grn)}.ag-sig.bear{color:var(--red)}.ag-sig.hold{color:var(--gold)}.ag-sig.none{color:var(--dim)}
.ag-name{font-size:10px;font-weight:700;margin-bottom:2px;}
.ag-val{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);line-height:1.4;}
.ag-conf{font-family:'Share Tech Mono';font-size:7px;color:var(--blu);margin-top:2px;}
.ag-sect{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:2px;margin:9px 0 5px;}
.nambi-box{border-radius:13px;padding:16px;margin-bottom:9px;border:2px solid var(--brd);transition:all .4s;}
.nambi-box.buy-ce{border-color:rgba(0,230,118,.6);background:linear-gradient(135deg,rgba(0,230,118,.08),rgba(0,230,118,.01));box-shadow:0 0 40px rgba(0,230,118,.15);}
.nambi-box.buy-pe{border-color:rgba(255,23,68,.6);background:linear-gradient(135deg,rgba(255,23,68,.08),rgba(255,23,68,.01));box-shadow:0 0 40px rgba(255,23,68,.15);}
.nambi-box.wait{border-color:rgba(240,165,0,.5);}
.nambi-box.idle{background:var(--bg2);}
.nambi-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:3px;margin-bottom:5px;}
.nambi-sig{font-family:Orbitron;font-size:30px;font-weight:900;margin-bottom:4px;}
.nambi-conf{font-family:'Share Tech Mono';font-size:10px;color:var(--dim);margin-bottom:11px;}
.conf-track{height:12px;border-radius:6px;background:rgba(255,255,255,.05);overflow:hidden;display:flex;margin-bottom:5px;}
.conf-bull{height:100%;background:linear-gradient(90deg,#003d2e,var(--grn));transition:width .7s;}
.conf-bear{height:100%;background:linear-gradient(90deg,var(--red),#5a0000);transition:width .7s;}
.conf-pct{display:flex;justify-content:space-between;font-family:'Share Tech Mono';font-size:9px;margin-bottom:9px;}
.rsn-list{background:var(--bg3);border-radius:8px;padding:9px;}
.rsn-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:5px;}
.rsn-item{font-family:'Share Tech Mono';font-size:8px;padding:4px 0;border-bottom:1px solid rgba(30,45,61,.5);line-height:1.4;}
.rsn-item:last-child{border:none;}
.eng-row{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.eng-cell{background:var(--bg3);border:1px solid var(--brd);border-radius:9px;padding:10px;text-align:center;}
.eng-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:4px;}
.eng-val{font-family:Orbitron;font-size:12px;font-weight:700;margin-bottom:3px;}
.eng-r{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);line-height:1.4;}
.l17-row{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-bottom:9px;}
.l17c{background:var(--bg3);border-radius:7px;padding:7px;text-align:center;border:1px solid var(--brd);}
.l17n{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:2px;}
.l17v{font-family:Orbitron;font-size:14px;font-weight:700;}
.smsg{border-radius:8px;padding:10px 12px;margin-bottom:9px;font-family:'Share Tech Mono';font-size:10px;text-align:center;display:none;}
.wsbar{position:fixed;bottom:0;left:0;right:0;z-index:200;padding:5px 12px;font-family:'Share Tech Mono';font-size:9px;background:var(--bg2);border-top:1px solid var(--brd);display:flex;align-items:center;gap:6px;}
.wsdot{width:7px;height:7px;border-radius:50%;flex-shrink:0;}
.wsdot.on{background:var(--grn);animation:pulse 2s infinite;}
.wsdot.off{background:var(--red);}
.auto-row{display:flex;justify-content:space-between;align-items:center;background:var(--bg2);border:1px solid var(--brd);border-radius:7px;padding:8px 11px;margin-bottom:9px;font-family:'Share Tech Mono';font-size:9px;}
.tog{width:38px;height:22px;background:var(--bg3);border-radius:11px;border:1px solid var(--brd);cursor:pointer;position:relative;}
.tog.on{background:rgba(0,230,118,.2);border-color:var(--grn);}
.tog-dot{position:absolute;top:3px;left:3px;width:14px;height:14px;border-radius:50%;background:var(--dim);transition:.2s;}
.tog.on .tog-dot{left:19px;background:var(--grn);}
.go-btn{width:100%;padding:14px;border-radius:11px;border:none;cursor:pointer;background:linear-gradient(135deg,#7a5200,var(--gold),#f5c540);color:#000;font-family:Orbitron;font-size:11px;font-weight:900;letter-spacing:2px;margin-bottom:9px;}
.go-btn:disabled{background:#1a2230;color:var(--dim);}
.ki{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:6px;color:var(--grn);padding:9px;font-size:14px;font-family:'Share Tech Mono';outline:none;}
.claude-box{background:var(--bg2);border:1px solid rgba(240,165,0,.2);border-radius:11px;padding:12px;margin-bottom:9px;}
.claude-title{font-family:Orbitron;font-size:8px;color:var(--gold);margin-bottom:8px;}
.claude-text{font-size:13px;line-height:1.9;}

/* TABS */
.tabs{display:flex;gap:0;margin-bottom:9px;background:var(--bg2);border:1px solid var(--brd);border-radius:9px;padding:3px;overflow-x:auto;}
.tab{flex:1;padding:8px 4px;border-radius:7px;cursor:pointer;font-family:Orbitron;font-size:8px;letter-spacing:.5px;color:var(--dim);text-align:center;white-space:nowrap;border:none;background:transparent;min-width:60px;}
.tab.on{background:var(--gold);color:#000;font-weight:900;}
.tc{display:none;}.tc.on{display:block;}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo">MATHAN AI HEMAN<small>HIGH EFFICIENCY MARKET ADAPTIVE NETWORK</small></div>
  <div style="display:flex;align-items:center;gap:8px">
    <span class="hclock" id="clock">--:--:--</span>
    <span class="hlive off" id="live-badge">OFFLINE</span>
  </div>
</div>
<div class="sbar">
  <div><span class="sdot wait" id="sdot"></span><span id="stxt" style="color:var(--gold)">Loading...</span></div>
  <span id="rtxt" style="color:var(--dim)">IST</span>
</div>

<div class="main">
<div class="banner">
  <div class="btitle">HEMAN</div>
  <div class="bsub">MARKET BEHAVIOUR TRADING SYSTEM</div>
  <div style="font-family:'Share Tech Mono';font-size:8px;color:rgba(240,165,0,.5);margin-top:3px">CCS is BODY · AI Brain is SOUL · Live Data is BLOOD</div>
</div>

<div class="src-row none" id="src-row">
  <span id="src-lbl">NOT CONNECTED</span>
  <span id="src-cnt" style="color:var(--dim)">Cycle #0</span>
</div>

<div class="smsg" id="smsg"></div>

<div class="tabs" id="tabs">
  <button class="tab on" id="tab-market" onclick="showTab('market')">MARKET</button>
  <button class="tab" id="tab-agents" onclick="showTab('agents')">AGENTS</button>
  <button class="tab" id="tab-engines" onclick="showTab('engines')">ENGINES</button>
  <button class="tab" id="tab-setup" onclick="showTab('setup')">SETUP</button>
</div>

<!-- MARKET -->
<div class="tc on" id="tc-market">
  <div class="idx-row">
    <div class="ib on" id="ib-NIFTY" onclick="setIdx('NIFTY')"><div class="ib-name">NIFTY 50</div><div class="ib-spot" id="n-spot">—</div><div class="ib-atm" id="n-atm">ATM: —</div></div>
    <div class="ib" id="ib-SENSEX" onclick="setIdx('SENSEX')"><div class="ib-name">SENSEX</div><div class="ib-spot" id="s-spot">—</div><div class="ib-atm" id="s-atm">ATM: —</div></div>
  </div>
  <div class="mstrip">
    <div class="mc"><div class="mc-n">SPOT</div><div class="mc-v" id="nv" style="color:var(--grn)">—</div></div>
    <div class="mc"><div class="mc-n">VIX</div><div class="mc-v" id="vv" style="color:var(--gold)">—</div></div>
    <div class="mc"><div class="mc-n">CYCLE</div><div class="mc-v" id="cyc" style="color:var(--pur)">0</div></div>
  </div>
  <div class="card">
    <div class="ctitle">OI ANALYSIS <span class="badge wait" id="oi-badge">LOADING</span></div>
    <div class="oi-grid">
      <div class="oi-cell"><div class="oi-lbl">CALL OI</div><div class="oi-val" id="callOI" style="color:var(--red)">—</div></div>
      <div class="oi-cell"><div class="oi-lbl">PUT OI</div><div class="oi-val" id="putOI" style="color:var(--grn)">—</div></div>
    </div>
    <div class="pcr-wrap">
      <div class="pcr-lbl"><span>PCR</span><span id="pcrVal" style="color:var(--gold)">—</span></div>
      <div class="pcr-bg"><div class="pcr-fill" id="pcrFill" style="width:50%;background:var(--gold)"></div></div>
      <div class="pcr-marks"><span>BEAR</span><span>1.0</span><span>BULL</span></div>
    </div>
    <div class="sr-row">
      <div class="sr-cell sr-sup"><div class="sr-lbl" style="color:var(--grn)">SUPPORT</div><div class="sr-val" id="sup" style="color:var(--grn)">—</div><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--dim)" id="supOI">—</div></div>
      <div class="sr-cell sr-res"><div class="sr-lbl" style="color:var(--red)">RESISTANCE</div><div class="sr-val" id="res" style="color:var(--red)">—</div><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--dim)" id="resOI">—</div></div>
    </div>
  </div>
  <div class="card">
    <div class="ctitle">ATM PREMIUM</div>
    <div class="prem-grid">
      <div class="prem-cell"><div class="ptype" style="color:var(--grn)">CALL CE</div><div class="pval" id="ceVal" style="color:var(--grn)">—</div><div class="pchg" id="ceChg">—</div></div>
      <div class="prem-cell"><div class="ptype" style="color:var(--red)">PUT PE</div><div class="pval" id="peVal" style="color:var(--red)">—</div><div class="pchg" id="peChg">—</div></div>
    </div>
  </div>
  <div class="nambi-box idle" id="nambi-box">
    <div class="nambi-lbl">L14 NAMBI MASTER CONTROLLER</div>
    <div class="nambi-sig" id="nambi-sig" style="color:var(--dim)">AWAITING DATA</div>
    <div class="nambi-conf" id="nambi-conf">Connect Angel One to begin</div>
    <div class="conf-track"><div class="conf-bull" id="conf-bull" style="width:50%"></div><div class="conf-bear" id="conf-bear" style="width:50%"></div></div>
    <div class="conf-pct"><span id="bull-pct" style="color:var(--grn)">BULL 50%</span><span id="bear-pct" style="color:var(--red)">BEAR 50%</span></div>
    <div class="rsn-list" id="rsn-list" style="display:none"><div class="rsn-lbl">SIGNAL SOURCES</div><div id="reasons"></div></div>
  </div>
  <div class="auto-row"><span>Auto refresh 5s</span><div class="tog on" id="auto-tog" onclick="toggleAuto()"><div class="tog-dot"></div></div></div>
  <button class="btn btn-blu" style="margin-bottom:9px" onclick="fetchNow()">FETCH LIVE DATA NOW</button>
</div>

<!-- AGENTS -->
<div class="tc" id="tc-agents">
  <div class="ag-sect">OI + PRICE + MACRO</div>
  <div class="ag-grid">
    <div class="agc" id="ag-l1"><div class="ag-top"><span class="ag-id">L1</span><span class="ag-sig none" id="sig-l1">—</span></div><div class="ag-name">OI Analyst</div><div class="ag-val" id="det-l1">—</div><div class="ag-conf" id="conf-l1"></div></div>
    <div class="agc" id="ag-l2"><div class="ag-top"><span class="ag-id">L2</span><span class="ag-sig none" id="sig-l2">—</span></div><div class="ag-name">Price Action</div><div class="ag-val" id="det-l2">—</div><div class="ag-conf" id="conf-l2"></div></div>
    <div class="agc" id="ag-l3"><div class="ag-top"><span class="ag-id">L3</span><span class="ag-sig none" id="sig-l3">—</span></div><div class="ag-name">VIX Monitor</div><div class="ag-val" id="det-l3">—</div><div class="ag-conf" id="conf-l3"></div></div>
    <div class="agc" id="ag-l4"><div class="ag-top"><span class="ag-id">L4</span><span class="ag-sig none" id="sig-l4">—</span></div><div class="ag-name">GIFT Tracker</div><div class="ag-val" id="det-l4">—</div><div class="ag-conf" id="conf-l4"></div></div>
  </div>
  <div class="ag-sect">PREMIUM + SESSION</div>
  <div class="ag-grid">
    <div class="agc" id="ag-l5"><div class="ag-top"><span class="ag-id">L5</span><span class="ag-sig none" id="sig-l5">—</span></div><div class="ag-name">CE Premium</div><div class="ag-val" id="det-l5">—</div><div class="ag-conf" id="conf-l5"></div></div>
    <div class="agc" id="ag-l6"><div class="ag-top"><span class="ag-id">L6</span><span class="ag-sig none" id="sig-l6">—</span></div><div class="ag-name">PE Premium</div><div class="ag-val" id="det-l6">—</div><div class="ag-conf" id="conf-l6"></div></div>
    <div class="agc" id="ag-l7"><div class="ag-top"><span class="ag-id">L7</span><span class="ag-sig none" id="sig-l7">—</span></div><div class="ag-name">Session Clock</div><div class="ag-val" id="det-l7">—</div><div class="ag-conf" id="conf-l7"></div></div>
    <div class="agc" id="ag-l8"><div class="ag-top"><span class="ag-id">L8</span><span class="ag-sig none" id="sig-l8">—</span></div><div class="ag-name">Expiry Watcher</div><div class="ag-val" id="det-l8">—</div><div class="ag-conf" id="conf-l8"></div></div>
  </div>
  <div class="ag-sect">BEHAVIOUR + INTELLIGENCE</div>
  <div class="ag-grid">
    <div class="agc" id="ag-l9"><div class="ag-top"><span class="ag-id">L9</span><span class="ag-sig none" id="sig-l9">—</span></div><div class="ag-name">Gap Detector</div><div class="ag-val" id="det-l9">—</div><div class="ag-conf" id="conf-l9"></div></div>
    <div class="agc" id="ag-l10"><div class="ag-top"><span class="ag-id">L10</span><span class="ag-sig none" id="sig-l10">—</span></div><div class="ag-name">PCR Engine</div><div class="ag-val" id="det-l10">—</div><div class="ag-conf" id="conf-l10"></div></div>
    <div class="agc" id="ag-l11"><div class="ag-top"><span class="ag-id">L11</span><span class="ag-sig none" id="sig-l11">—</span></div><div class="ag-name">Trap Detector</div><div class="ag-val" id="det-l11">—</div><div class="ag-conf" id="conf-l11"></div></div>
    <div class="agc" id="ag-l12"><div class="ag-top"><span class="ag-id">L12</span><span class="ag-sig none" id="sig-l12">—</span></div><div class="ag-name">Risk Control</div><div class="ag-val" id="det-l12">—</div><div class="ag-conf" id="conf-l12"></div></div>
  </div>
  <div class="ag-sect">L13 MASTER BEHAVIOUR AI</div>
  <div class="agc" id="ag-l13" style="padding:11px;margin-bottom:9px">
    <div class="ag-top"><span class="ag-id" style="font-size:9px">L13</span><span class="ag-sig none" id="sig-l13" style="font-size:13px">—</span></div>
    <div class="ag-name" style="font-size:12px;margin-bottom:3px">Behaviour AI</div>
    <div class="ag-val" id="det-l13">—</div><div class="ag-conf" id="conf-l13"></div>
  </div>
  <div class="card">
    <div class="ctitle">L17 SELF LEARNING</div>
    <div class="l17-row">
      <div class="l17c"><div class="l17n">TRADES</div><div class="l17v" id="l17t" style="color:var(--gold)">0</div></div>
      <div class="l17c"><div class="l17n">WINS</div><div class="l17v" id="l17w" style="color:var(--grn)">0</div></div>
      <div class="l17c"><div class="l17n">LOSS</div><div class="l17v" id="l17l" style="color:var(--red)">0</div></div>
      <div class="l17c"><div class="l17n">WIN%</div><div class="l17v" id="l17r" style="color:var(--blu)">0%</div></div>
    </div>
  </div>
</div>

<!-- ENGINES -->
<div class="tc" id="tc-engines">
  <div class="eng-row">
    <div class="eng-cell"><div class="eng-lbl">L15 TRUTH ENGINE</div><div class="eng-val" id="l15v" style="color:var(--dim)">—</div><div class="eng-r" id="l15r">Awaiting data</div></div>
    <div class="eng-cell"><div class="eng-lbl">L16 CONTRADICTION</div><div class="eng-val" id="l16v" style="color:var(--dim)">—</div><div class="eng-r" id="l16a">Awaiting data</div></div>
  </div>
  <div class="card"><div class="ctitle">L16 SMART MONEY DETAIL</div><div style="font-family:'Share Tech Mono';font-size:9px;line-height:1.6" id="l16d">Awaiting OI data...</div></div>
  <div class="card">
    <div class="ctitle">SYSTEM STATUS</div>
    <div style="font-family:'Share Tech Mono';font-size:10px;line-height:2">
      <div>Angel One: <span id="sys-angel" style="color:var(--dim)">—</span></div>
      <div>WebSocket: <span id="sys-ws" style="color:var(--dim)">—</span></div>
      <div>Data Source: <span id="sys-src" style="color:var(--dim)">—</span></div>
      <div>Last Fetch: <span id="sys-ft" style="color:var(--dim)">—</span></div>
      <div>Error: <span id="sys-err" style="color:var(--red)">—</span></div>
    </div>
  </div>
</div>

<!-- SETUP -->
<div class="tc" id="tc-setup">
  <div class="card" style="border-color:rgba(206,147,216,.4)">
    <div class="ctitle" style="color:var(--pur)">ANGEL ONE LIVE DATA
      <span id="angel-st" style="font-family:'Share Tech Mono';font-size:8px;color:var(--dim)">NOT SET</span>
    </div>
    <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-bottom:10px">Saved in server DB. Auto-loads on restart.</div>
    <div class="lbl">API KEY</div>
    <input class="inp" id="api-key" type="password" placeholder="Your API Key">
    <div class="lbl">CLIENT ID</div>
    <input class="inp" id="client-id" type="text" placeholder="A12345">
    <div class="lbl">PIN (4-digit)</div>
    <input class="inp" id="angel-pin" type="password" placeholder="1234">
    <div class="lbl">TOTP SECRET</div>
    <input class="inp" id="totp-secret" type="password" placeholder="JBSWY3DPEHPK3PXP">
    <button class="btn btn-pur" id="conn-btn" onclick="connectAngel()">CONNECT ANGEL ONE</button>
  </div>
  <div class="card" style="border-color:rgba(41,182,246,.3)">
    <div class="ctitle" style="color:var(--blu)">TELEGRAM ALERTS
      <span id="tg-st" style="font-family:'Share Tech Mono';font-size:8px;color:var(--dim)">OFF</span>
    </div>
    <div class="lbl">BOT TOKEN</div>
    <input class="inp" id="tg-token" type="password" placeholder="1234567890:AAB...">
    <div class="lbl">CHAT ID</div>
    <input class="inp" id="tg-chat" type="text" placeholder="-100123456789">
    <button class="btn btn-ora" onclick="saveTG()">SAVE AND TEST</button>
  </div>
  <div class="card">
    <div class="ctitle">CAPITAL</div>
    <input class="inp" id="cap-inp" type="number" placeholder="10000" value="10000">
    <button class="btn btn-grn" onclick="saveCap()">SAVE CAPITAL</button>
  </div>
  <div class="card" style="border-color:rgba(240,165,0,.25)">
    <div class="ctitle" style="color:var(--gold)">CLAUDE AI KEY</div>
    <input class="ki" id="ki" type="password" placeholder="sk-ant-api03-..." oninput="saveKey()">
    <div id="kst" style="font-family:'Share Tech Mono';font-size:9px;margin-top:4px;color:var(--grn)"></div>
  </div>
  <div style="display:flex;gap:7px;margin-bottom:9px">
    <input style="flex:1;background:var(--bg3);border:1px solid var(--brd);border-radius:7px;color:var(--txt);padding:10px;font-size:15px;font-family:'Share Tech Mono';outline:none" id="cap" type="number" placeholder="Capital Rs" value="10000">
    <button class="btn btn-ora" style="width:auto;padding:10px 14px;margin:0" onclick="runTrade()">PLAN</button>
  </div>
  <button class="go-btn" id="go-btn" onclick="runClaude()">NAMBI + CLAUDE FULL STRATEGY</button>
  <div class="claude-box" id="claude-box" style="display:none">
    <div class="claude-title">CLAUDE AI HEMAN STRATEGY</div>
    <div class="claude-text" id="claude-text"></div>
  </div>
</div>
</div>

<div class="wsbar">
  <div class="wsdot off" id="wsdot"></div>
  <span id="ws-txt">Starting...</span>
  <span style="margin-left:auto;color:var(--dim);font-size:8px" id="poll-cnt"></span>
</div>

<script>
var autoOn=true,timer=null,SS={},pct=0;

function showTab(id){
  var tabs=['market','agents','engines','setup'];
  for(var i=0;i<tabs.length;i++){
    var t=tabs[i];
    var btn=document.getElementById('tab-'+t);
    var pane=document.getElementById('tc-'+t);
    if(t===id){btn.className='tab on';pane.className='tc on';}
    else{btn.className='tab';pane.className='tc';}
  }
}

function q(id){return document.getElementById(id);}
function tx(id,v){var e=q(id);if(e)e.textContent=v;}
function fmtOI(n){if(!n&&n!==0)return'—';if(n>10000000)return(n/10000000).toFixed(1)+'Cr';if(n>100000)return(n/100000).toFixed(1)+'L';if(n>1000)return(n/1000).toFixed(1)+'K';return''+n;}

function showMsg(msg,col){
  var d=q('smsg');d.textContent=msg;d.style.display='block';
  var bg={grn:'rgba(0,230,118,.12)',red:'rgba(255,23,68,.12)',blu:'rgba(41,182,246,.1)',ora:'rgba(255,152,0,.1)'};
  var tc={grn:'#00e676',red:'#ff1744',blu:'#29b6f6',ora:'#ff9800'};
  d.style.background=bg[col]||bg.blu;d.style.color=tc[col]||tc.blu;
  setTimeout(function(){d.style.display='none';},6000);
}

function pollState(){
  fetch('/api/state',{cache:'no-store'})
  .then(function(r){return r.json();})
  .then(function(s){
    pct++;
    q('wsdot').className='wsdot on';
    q('live-badge').className='hlive on';q('live-badge').textContent='LIVE';
    q('ws-txt').textContent='Connected';
    q('poll-cnt').textContent='Poll #'+pct;
    q('sdot').className='sdot ok';
    applyState(s);
  })
  .catch(function(){
    q('wsdot').className='wsdot off';
    q('live-badge').className='hlive off';q('live-badge').textContent='OFFLINE';
    q('ws-txt').textContent='Reconnecting...';
    q('sdot').className='sdot wait';
    tx('stxt','Server offline — retrying...');
  });
}

function startPoll(){
  if(timer)clearInterval(timer);
  pollState();
  timer=setInterval(function(){if(autoOn)pollState();},5000);
}

function toggleAuto(){
  autoOn=!autoOn;
  q('auto-tog').className='tog'+(autoOn?' on':'');
  if(autoOn)startPoll();
}

function fetchNow(){
  fetch('/api/fetch',{method:'POST'}).catch(function(){});
  setTimeout(pollState,1500);
}

function setIdx(i){
  fetch('/api/set_index',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:i})})
  .catch(function(){});
  q('ib-NIFTY').className='ib'+(i==='NIFTY'?' on':'');
  q('ib-SENSEX').className='ib'+(i==='SENSEX'?' on':'');
  setTimeout(pollState,1000);
}

function connectAngel(){
  var ak=q('api-key').value.trim();
  var ci=q('client-id').value.trim();
  var pin=q('angel-pin').value.trim();
  var ts=q('totp-secret').value.trim();
  if(!ak||!ci||!pin||!ts){showMsg('All 4 fields required','red');return;}
  var btn=q('conn-btn');btn.disabled=true;btn.textContent='CONNECTING...';
  showMsg('Connecting to Angel One...','blu');
  fetch('/connect_angel',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({api_key:ak,client_id:ci,pin:pin,totp_secret:ts})})
  .then(function(r){return r.json();})
  .then(function(d){
    if(d.ok){
      showMsg('Login started — loading option chain...','grn');
      localStorage.setItem('a_ak',ak);localStorage.setItem('a_ci',ci);
      localStorage.setItem('a_pin',pin);localStorage.setItem('a_ts',ts);
      setTimeout(pollState,3000);
      setTimeout(pollState,8000);
      setTimeout(pollState,15000);
    }else{showMsg('Error: '+d.error,'red');}
  })
  .catch(function(e){showMsg('Network error: '+e.message,'red');})
  .finally(function(){btn.disabled=false;btn.textContent='CONNECT ANGEL ONE';});
}

function saveTG(){
  var tt=q('tg-token').value.trim();var tc=q('tg-chat').value.trim();
  if(!tt||!tc){showMsg('Token and Chat ID required','red');return;}
  fetch('/api/set_telegram',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({token:tt,chat_id:tc})})
  .then(function(r){return r.json();})
  .then(function(d){if(d.ok){tx('tg-st','ON');showMsg('Telegram connected!','grn');}})
  .catch(function(){});
}

function saveCap(){
  var cap=parseFloat(q('cap-inp').value||10000);
  fetch('/api/set_capital',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({capital:cap})}).catch(function(){});
  showMsg('Capital saved Rs '+cap,'grn');
}

function saveKey(){
  var k=q('ki').value.trim();
  if(k){localStorage.setItem('mbk',k);tx('kst','Saved');}
}

function loadSaved(){
  var k=localStorage.getItem('mbk');if(k){q('ki').value=k;tx('kst','Loaded');}
  var ak=localStorage.getItem('a_ak');if(ak)q('api-key').value=ak;
  var ci=localStorage.getItem('a_ci');if(ci)q('client-id').value=ci;
  var pin=localStorage.getItem('a_pin');if(pin)q('angel-pin').value=pin;
  var ts=localStorage.getItem('a_ts');if(ts)q('totp-secret').value=ts;
}

function applyState(s){
  if(!s)return;
  SS=s;
  var mk=s.market||{};var sys=s.sys||{};
  var sp=mk.spot,atm=mk.atm,pcr=mk.pcr;
  tx('nv',sp?sp.toFixed(0):'—');
  tx('n-spot',sp?sp.toFixed(0):'—');tx('n-atm',atm?'ATM:'+atm:'ATM:—');
  tx('s-spot',sp?sp.toFixed(0):'—');tx('s-atm',atm?'ATM:'+atm:'ATM:—');
  tx('vv',mk.vix?mk.vix.toFixed(1):'—');
  tx('callOI',fmtOI(mk.call_oi));tx('putOI',fmtOI(mk.put_oi));
  tx('sup',mk.support||'—');tx('res',mk.resistance||'—');
  tx('supOI',fmtOI(mk.sup_oi));tx('resOI',fmtOI(mk.res_oi));
  if(pcr){
    tx('pcrVal',pcr.toFixed(2));
    var fill=Math.min(100,Math.max(0,(pcr-0.5)/1.5*100));
    q('pcrFill').style.width=fill+'%';
    q('pcrFill').style.background=pcr>1.2?'var(--grn)':pcr<0.8?'var(--red)':'var(--gold)';
  }
  var ce=mk.ce_prem,pe=mk.pe_prem,cep=mk.ce_prev,pep=mk.pe_prev;
  tx('ceVal',ce?'Rs'+ce.toFixed(0):'—');tx('peVal',pe?'Rs'+pe.toFixed(0):'—');
  if(ce&&cep){var cc=ce-cep;tx('ceChg',(cc>=0?'+':'')+cc.toFixed(1));q('ceChg').style.color=cc>0?'var(--grn)':'var(--red)';}
  if(pe&&pep){var pc2=pe-pep;tx('peChg',(pc2>=0?'+':'')+pc2.toFixed(1));q('peChg').style.color=pc2>0?'var(--red)':'var(--grn)';}
  tx('cyc',sys.count||0);
  if(sys.source==='ANGEL ONE'){
    q('src-row').className='src-row live';tx('src-lbl','ANGEL ONE LIVE');
    q('sdot').className='sdot ok';tx('stxt','Angel One Live');
    q('stxt').style.color='var(--grn)';
  }else{
    q('src-row').className='src-row none';tx('src-lbl','NOT CONNECTED');
    tx('stxt','Waiting — enter credentials in SETUP');q('stxt').style.color='var(--gold)';
  }
  tx('src-cnt','Cycle #'+(sys.count||0));
  var ags=s.agents||{};
  for(var id in ags)updateAgent(id,ags[id]);
  if(s.nambi)applyNambi(s.nambi);
  var l15=s.l15||{};
  tx('l15v',l15.verdict||'—');
  q('l15v').style.color=l15.verdict==='TRUE_MOVE'?'var(--grn)':l15.verdict==='FAKE_MOVE'?'var(--red)':l15.verdict==='TRAP'?'var(--orn)':'var(--dim)';
  tx('l15r',l15.reason||'Awaiting data');
  var l16=s.l16||{};
  tx('l16v',l16.trap_status||'—');
  q('l16v').style.color=(l16.trap_status==='CALL_TRAP'||l16.trap_status==='PUT_TRAP')?'var(--red)':l16.trap_status==='TRUE_MOVE'?'var(--grn)':'var(--dim)';
  tx('l16a',l16.action||'—');tx('l16d',l16.reason||'Awaiting OI data');
  var l17=s.l17||{};
  tx('l17t',l17.total_trades||0);tx('l17w',l17.wins||0);tx('l17l',l17.losses||0);tx('l17r',(l17.win_rate||0)+'%');
  var ang=s.angel||{};
  tx('sys-angel',ang.connected?'Connected: '+ang.client_id:'Not connected');
  q('sys-angel').style.color=ang.connected?'var(--grn)':'var(--red)';
  tx('sys-ws',ang.ws_running?'Live':'Stopped');
  q('sys-ws').style.color=ang.ws_running?'var(--grn)':'var(--red)';
  tx('sys-src',sys.source||'NONE');tx('sys-ft',mk.fetch_time||'—');
  tx('sys-err',ang.error||'None');
  if(ang.connected)tx('angel-st','Connected: '+ang.client_id);
  if(s.telegram&&s.telegram.enabled)tx('tg-st','ON');
  if(mk.call_oi){q('oi-badge').className='badge live';tx('oi-badge','LIVE');}
}

function updateAgent(id,ag){
  var sig=ag.signal||'none';
  var el=q('ag-'+id);
  if(el)el.className='agc '+sig;
  var sc=q('sig-'+id);
  if(sc){sc.textContent=sig==='bull'?'BULL':sig==='bear'?'BEAR':sig==='hold'?'HOLD':'—';sc.className='ag-sig '+sig;}
  tx('det-'+id,ag.detail||'—');
  tx('conf-'+id,ag.confidence?'Conf: '+ag.confidence+'%':'');
}

function applyNambi(n){
  if(!n)return;
  var sig=n.signal||'WAIT';
  var box=q('nambi-box');
  box.className='nambi-box '+(sig==='BUY CE'?'buy-ce':sig==='BUY PE'?'buy-pe':sig==='WAIT'?'wait':'idle');
  var sc=q('nambi-sig');sc.textContent=sig;
  sc.style.color=sig==='BUY CE'?'var(--grn)':sig==='BUY PE'?'var(--red)':'var(--gold)';
  tx('nambi-conf',n.confidence+' CONFIDENCE'+(n.trap_detected?' | TRAP DETECTED':'')+(n.conflict?' | CONFLICTED':''));
  q('conf-bull').style.width=(n.bull_pct||50)+'%';
  q('conf-bear').style.width=(n.bear_pct||50)+'%';
  tx('bull-pct','BULL '+(n.bull_pct||50)+'%');
  tx('bear-pct','BEAR '+(n.bear_pct||50)+'%');
  var rl=q('rsn-list');
  if(n.reasons&&n.reasons.length>0){
    rl.style.display='block';
    var html='';
    for(var i=0;i<n.reasons.length;i++)html+='<div class="rsn-item">'+n.reasons[i]+'</div>';
    q('reasons').innerHTML=html;
  }else rl.style.display='none';
}

function runClaude(){
  var key=localStorage.getItem('mbk');
  if(!key){alert('SETUP tab > Claude API Key enter pannunga');return;}
  var btn=q('go-btn');btn.disabled=true;btn.textContent='Analysing...';
  q('claude-box').style.display='block';
  var ct=q('claude-text');ct.textContent='HEMAN analysing...';
  var s=SS;var mk=s.market||{};var nb=s.nambi||{};var l16=s.l16||{};var l15=s.l15||{};
  var prompt='You are Nambi from Mathan AI HEMAN — Behaviour Intelligence Trading Engine.\n'
    +'LIVE DATA: Index:'+(s.sys?s.sys.index:'NIFTY')+' Spot:'+(mk.spot?mk.spot.toFixed(0):'—')+' ATM:'+(mk.atm||'—')+'\n'
    +'VIX:'+(mk.vix?mk.vix.toFixed(1):'—')+' PCR:'+(mk.pcr?mk.pcr.toFixed(2):'—')+'\n'
    +'Call OI:'+(mk.call_oi||'—')+' Put OI:'+(mk.put_oi||'—')+'\n'
    +'CE:Rs'+(mk.ce_prem?mk.ce_prem.toFixed(0):'—')+' PE:Rs'+(mk.pe_prem?mk.pe_prem.toFixed(0):'—')+'\n'
    +'Support:'+(mk.support||'—')+' Resistance:'+(mk.resistance||'—')+'\n'
    +'NAMBI:'+(nb.signal||'WAIT')+' Confidence:'+(nb.confidence||'—')+' Bull:'+(nb.bull_pct||50)+'% Bear:'+(nb.bear_pct||50)+'%\n'
    +'L15:'+(l15.verdict||'—')+' L16:'+(l16.trap_status||'—')+' Action:'+(l16.action||'—')+'\n'
    +'Capital:Rs'+(q('cap').value||10000)+'\n'
    +'Give precise strategy: Entry strike, Premium, SL, Target, Lots. Max 150 words. Direct.';
  fetch('https://api.anthropic.com/v1/messages',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({model:'claude-sonnet-4-20250514',max_tokens:1000,messages:[{role:'user',content:prompt}]})
  })
  .then(function(r){return r.json();})
  .then(function(d){
    var txt=d.content?d.content.map(function(i){return i.text||'';}).join(''):'No response';
    ct.innerHTML=txt.replace(/\n/g,'<br>');
  })
  .catch(function(e){ct.textContent='Error: '+e.message;})
  .finally(function(){btn.disabled=false;btn.textContent='NAMBI + CLAUDE FULL STRATEGY';});
}

function runTrade(){
  var s=SS;var mk=s.market||{};var nb=s.nambi||{};
  var cap=parseFloat(q('cap').value||10000);var sig=nb.signal||'WAIT';
  q('claude-box').style.display='block';var ct=q('claude-text');
  if(sig==='WAIT'){ct.textContent='NAMBI says WAIT — No trade now.';return;}
  var lot=s.sys&&s.sys.index==='NIFTY'?75:20;
  var price=sig==='BUY CE'?mk.ce_prem:mk.pe_prem;
  if(!price){ct.textContent='Premium not available.';return;}
  var lots=Math.max(1,Math.floor(cap/(price*lot)));
  var sl=(price*0.35).toFixed(0);var tgt=(price*1.6).toFixed(0);
  ct.innerHTML='<b>'+sig+'</b> ATM '+mk.atm+'<br>Premium: Rs'+price.toFixed(0)+'<br>Lots: '+lots+'<br>SL: Rs'+sl+' | Target: Rs'+tgt+'<br>Risk: Rs'+(lots*lot*(price-sl)).toFixed(0)+' | Reward: Rs'+(lots*lot*(tgt-price)).toFixed(0);
}

setInterval(function(){
  var n=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Kolkata'}));
  var p=function(v){return String(v).padStart(2,'0');};
  tx('clock',p(n.getHours())+':'+p(n.getMinutes())+':'+p(n.getSeconds()));
  tx('rtxt','IST '+p(n.getHours())+':'+p(n.getMinutes()));
},1000);

window.onload=function(){loadSaved();startPoll();};
</script>
</body>
</html>"""

if __name__ == "__main__":
    log.info("MATHAN AI HEMAN — Starting...")
    db_init();db_load();l17_load()
    if all([ANGEL["api_key"],ANGEL["client_id"],ANGEL["pin"],ANGEL["totp_secret"]]):
        log.info("[STARTUP] Auto-connecting Angel One...")
        threading.Thread(target=do_angel_connect,
            args=(ANGEL["api_key"],ANGEL["client_id"],ANGEL["pin"],ANGEL["totp_secret"]),
            daemon=True).start()
    threading.Thread(target=push_loop,daemon=True).start()
    threading.Thread(target=poll_loop,daemon=True).start()
    log.info("http://0.0.0.0:"+str(PORT))
    app.run(host="0.0.0.0",port=PORT,use_reloader=False,threaded=True)
