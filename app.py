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
sock=Sock(app)

@sock.route("/ws")
def ws_handler(ws):
    cl_add(ws)
    try:
        send1(ws,{"type":"connected","ts":ist()})
        send1(ws,{"type":"full_state","state":build_state()})
        with CCS_LOCK:recent=list(CCS_LOG[-20:])
        send1(ws,{"type":"ccs_history","events":recent})
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
                if not all([ak,ci,pin,ts2]):send1(ws,{"type":"angel_err","msg":"All 4 fields required"});continue
                threading.Thread(target=do_angel_connect,args=(ak,ci,pin,ts2),daemon=True).start()
            elif t=="set_index":
                idx=d.get("index","NIFTY").upper()
                if idx in INDEX_CFG:
                    with state_lock:SYS["index"]=idx
                    db_set("index",idx)
                    threading.Thread(target=full_cycle,daemon=True).start()
            elif t=="fetch":threading.Thread(target=full_cycle,daemon=True).start()
            elif t=="set_auto":SYS["auto"]=bool(d.get("on",True))
            elif t=="set_telegram":
                tt=d.get("token","").strip();tc=d.get("chat_id","").strip()
                if tt and tc:
                    TELEGRAM["token"]=tt;TELEGRAM["chat_id"]=tc;TELEGRAM["enabled"]=True
                    db_set("tg_token",tt);db_set("tg_chat",tc)
                    tg_alert("✅ HEMAN Telegram connected!")
                    send1(ws,{"type":"tg_ok","ts":ist()})
            elif t=="set_capital":
                try:EXEC["capital"]=float(d.get("capital",10000));db_set("capital",EXEC["capital"])
                except:pass
            elif t=="get_state":send1(ws,{"type":"full_state","state":build_state()})
            elif t=="get_ccs_log":
                with CCS_LOCK:recent=list(CCS_LOG[-50:])
                send1(ws,{"type":"ccs_history","events":recent})
    except Exception as e:log.error(f"[WS ERR]{e}")
    finally:cl_rm(ws)

@app.route("/connect_angel",methods=["POST"])
def connect_angel_rest():
    d=request.get_json(force=True) or {}
    ak=d.get("api_key","").strip();ci=d.get("client_id","").strip()
    pin=d.get("pin","").strip();ts=d.get("totp_secret","").strip()
    if not all([ak,ci,pin,ts]):return jsonify({"ok":False,"error":"All 4 required"}),400
    threading.Thread(target=do_angel_connect,args=(ak,ci,pin,ts),daemon=True).start()
    return jsonify({"ok":True,"msg":"Login started"})

@app.route("/ping")
def ping():
    return jsonify({"pong":True,"time":ist(),"angel":ANGEL["connected"],
                    "ws":ANGEL["ws_running"],"system":"MATHAN AI HEMAN"})

@app.route("/status")
def status():return jsonify(build_state())

@app.route("/ccs")
def ccs():
    with CCS_LOCK:return jsonify({"events":list(CCS_LOG)})

@app.route("/")
@app.route("/dashboard")
def dashboard():
    return Response(DASHBOARD_HTML,mimetype="text/html")


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<title>MATHAN AI HEMAN</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet"/>
<style>
:root{--bg:#060a0e;--bg2:#0c1218;--bg3:#101820;--brd:#1a2835;--gold:#f0a500;--grn:#00e676;--red:#ff1744;--blu:#29b6f6;--pur:#ce93d8;--orn:#ff9800;--txt:#cdd9e5;--dim:#3a5268;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--txt);font-family:'Rajdhani',sans-serif;padding-bottom:50px;}
body::before{content:'';position:fixed;inset:0;background:linear-gradient(rgba(240,165,0,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(240,165,0,.018) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.15}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(0,230,118,.4)}70%{box-shadow:0 0 0 8px rgba(0,230,118,0)}}
@keyframes spin{to{transform:rotate(360deg)}}
.hdr{position:sticky;top:0;z-index:100;background:linear-gradient(180deg,#080d12,rgba(6,10,14,.98));border-bottom:2px solid var(--gold);padding:10px 14px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 4px 32px rgba(240,165,0,.2);}
.logo{font-family:'Orbitron';font-size:12px;font-weight:900;color:var(--gold);letter-spacing:2px;}
.logo small{display:block;font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-top:2px;}
.hclock{font-family:'Orbitron';font-size:13px;color:var(--gold);}
.hlive{font-size:9px;font-family:'Share Tech Mono';padding:2px 8px;border-radius:3px;}
.hlive.on{border:1px solid var(--grn);color:var(--grn);}
.hlive.off{border:1px solid var(--red);color:var(--red);}
.sbar{display:flex;justify-content:space-between;padding:4px 12px;background:var(--bg2);border-bottom:1px solid var(--brd);font-family:'Share Tech Mono';font-size:9px;}
.sdot{width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:middle;}
.sdot.ok{background:var(--grn);animation:pulse 2s infinite;}
.sdot.wait{background:var(--gold);animation:blink 1s infinite;}
.main{padding:10px;max-width:480px;margin:0 auto;position:relative;z-index:1;}
.banner{background:linear-gradient(135deg,rgba(240,165,0,.07),rgba(240,165,0,.02));border:1px solid rgba(240,165,0,.3);border-radius:11px;padding:10px 14px;margin-bottom:9px;text-align:center;}
.btitle{font-family:'Orbitron';font-size:16px;font-weight:900;color:var(--gold);letter-spacing:3px;}
.bsub{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-top:3px;letter-spacing:2px;}
.btag{font-family:'Share Tech Mono';font-size:8px;color:rgba(240,165,0,.6);margin-top:3px;}
.src-row{display:flex;justify-content:space-between;padding:6px 11px;border-radius:7px;margin-bottom:9px;font-family:'Share Tech Mono';font-size:9px;border:1px solid var(--brd);background:var(--bg2);}
.src-row.live{border-color:rgba(0,230,118,.5);color:var(--grn);}
.src-row.none{border-color:rgba(255,23,68,.25);color:var(--red);}
.card{background:var(--bg2);border:1px solid var(--brd);border-radius:12px;padding:12px;margin-bottom:9px;}
.ctitle{font-family:'Orbitron';font-size:9px;color:var(--gold);letter-spacing:1px;margin-bottom:9px;display:flex;justify-content:space-between;align-items:center;}
.badge{display:inline-flex;padding:1px 7px;border-radius:8px;font-family:'Share Tech Mono';font-size:7px;}
.badge.live{background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.3);color:var(--grn);}
.badge.wait{background:rgba(41,182,246,.08);border:1px solid rgba(41,182,246,.2);color:var(--blu);}
.badge.err{background:rgba(255,23,68,.08);border:1px solid rgba(255,23,68,.2);color:var(--red);}
.inp{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:6px;color:var(--txt);padding:8px 10px;font-size:12px;font-family:'Share Tech Mono';outline:none;margin-bottom:6px;}
.inp:focus{border-color:var(--orn);}
.inp-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:.5px;margin-bottom:3px;}
.cbtn{width:100%;padding:11px;border-radius:8px;cursor:pointer;font-family:'Orbitron';font-size:9px;font-weight:700;letter-spacing:1px;border:1px solid var(--orn);background:rgba(255,152,0,.08);color:var(--orn);margin-top:6px;}
.cbtn.pur{border-color:var(--pur);background:rgba(206,147,216,.08);color:var(--pur);}
.cbtn.grn{border-color:var(--grn);background:rgba(0,230,118,.08);color:var(--grn);}
.idx-row{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.ib{background:var(--bg3);border:2px solid var(--brd);border-radius:9px;padding:9px;text-align:center;cursor:pointer;transition:.2s;}
.ib.on{border-color:var(--gold);}
.ib-name{font-family:'Orbitron';font-size:13px;font-weight:900;}
.ib.on .ib-name{color:var(--gold);}
.ib-spot{font-family:'Share Tech Mono';font-size:11px;color:var(--grn);margin-top:2px;}
.ib-atm{font-family:'Share Tech Mono';font-size:8px;color:var(--blu);margin-top:1px;}
.mstrip{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-bottom:9px;}
.mc{background:var(--bg2);border:1px solid var(--brd);border-radius:8px;padding:7px;text-align:center;}
.mc-n{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:2px;}
.mc-v{font-family:'Orbitron';font-size:13px;font-weight:700;}
.mc-c{font-family:'Share Tech Mono';font-size:8px;margin-top:1px;}
.oi-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.oi-cell{background:var(--bg3);border-radius:7px;padding:8px;text-align:center;border:1px solid var(--brd);}
.oi-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:2px;}
.oi-val{font-family:'Orbitron';font-size:14px;font-weight:700;}
.pcr-wrap{background:var(--bg3);border-radius:7px;padding:8px 9px;margin-bottom:7px;}
.pcr-lbl{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-bottom:5px;display:flex;justify-content:space-between;}
.pcr-bg{height:10px;border-radius:5px;background:rgba(255,255,255,.05);overflow:hidden;margin-bottom:4px;}
.pcr-fill{height:100%;border-radius:5px;transition:width .8s;}
.pcr-marks{display:flex;justify-content:space-between;font-family:'Share Tech Mono';font-size:7px;color:var(--dim);}
.sr-row{display:grid;grid-template-columns:1fr 1fr;gap:6px;}
.sr-cell{border-radius:7px;padding:8px;text-align:center;}
.sr-sup{background:rgba(0,230,118,.07);border:1px solid rgba(0,230,118,.2);}
.sr-res{background:rgba(255,23,68,.07);border:1px solid rgba(255,23,68,.2);}
.sr-lbl{font-family:'Share Tech Mono';font-size:7px;letter-spacing:.5px;margin-bottom:2px;}
.sr-val{font-family:'Orbitron';font-size:14px;font-weight:700;}
.prem-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.prem-cell{background:var(--bg3);border-radius:8px;padding:9px;border:2px solid var(--brd);text-align:center;transition:.3s;}
.ptype{font-family:'Orbitron';font-size:10px;font-weight:700;margin-bottom:3px;}
.pval{font-family:'Orbitron';font-size:22px;font-weight:700;}
.pchg{font-family:'Share Tech Mono';font-size:9px;margin-top:2px;}
.ag-sect{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:2px;margin:8px 0 5px;}
.ag-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:4px;}
.agc{background:var(--bg3);border:1px solid var(--brd);border-radius:8px;padding:8px;position:relative;overflow:hidden;transition:.3s;}
.agc::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--brd);}
.agc.bull::before{background:var(--grn);}
.agc.bear::before{background:var(--red);}
.agc.hold::before{background:var(--gold);}
.ag-top{display:flex;justify-content:space-between;margin-bottom:3px;}
.ag-id{font-family:'Orbitron';font-size:7px;color:var(--dim);}
.ag-sig{font-family:'Share Tech Mono';font-size:9px;font-weight:700;}
.ag-sig.bull{color:var(--grn);}.ag-sig.bear{color:var(--red);}.ag-sig.hold{color:var(--gold);}.ag-sig.none{color:var(--dim);}
.ag-name{font-size:10px;font-weight:700;margin-bottom:2px;}
.ag-val{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);line-height:1.3;}
.ag-conf{font-family:'Share Tech Mono';font-size:7px;color:var(--blu);margin-top:2px;}
.ag-w{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);}
.nambi-box{border-radius:13px;padding:16px;margin-bottom:9px;border:2px solid var(--brd);transition:all .4s;}
.nambi-box.buy-ce{border-color:rgba(0,230,118,.6);background:linear-gradient(135deg,rgba(0,230,118,.08),rgba(0,230,118,.01));box-shadow:0 0 40px rgba(0,230,118,.15);}
.nambi-box.buy-pe{border-color:rgba(255,23,68,.6);background:linear-gradient(135deg,rgba(255,23,68,.08),rgba(255,23,68,.01));box-shadow:0 0 40px rgba(255,23,68,.15);}
.nambi-box.wait{border-color:rgba(240,165,0,.5);background:linear-gradient(135deg,rgba(240,165,0,.07),rgba(240,165,0,.01));}
.nambi-box.idle{background:var(--bg2);}
.nambi-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:3px;margin-bottom:5px;}
.nambi-sig{font-family:'Orbitron';font-size:30px;font-weight:900;margin-bottom:3px;letter-spacing:2px;}
.nambi-conf{font-family:'Share Tech Mono';font-size:10px;color:var(--dim);margin-bottom:10px;}
.conf-track{height:12px;border-radius:6px;background:rgba(255,255,255,.05);overflow:hidden;display:flex;margin-bottom:5px;}
.conf-bull{height:100%;background:linear-gradient(90deg,#003d2e,var(--grn));transition:width .7s;}
.conf-bear{height:100%;background:linear-gradient(90deg,var(--red),#5a0000);transition:width .7s;}
.conf-pct{display:flex;justify-content:space-between;font-family:'Share Tech Mono';font-size:9px;margin-bottom:9px;}
.reason-list{background:var(--bg3);border-radius:8px;padding:9px;}
.reason-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:1px;margin-bottom:5px;}
.reason-item{font-family:'Share Tech Mono';font-size:8px;padding:4px 0;border-bottom:1px solid rgba(30,45,61,.5);color:var(--txt);line-height:1.4;}
.reason-item:last-child{border:none;}
.eng-row{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.eng-cell{background:var(--bg3);border:1px solid var(--brd);border-radius:9px;padding:9px;text-align:center;}
.eng-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:1px;margin-bottom:4px;}
.eng-val{font-family:'Orbitron';font-size:11px;font-weight:700;margin-bottom:3px;}
.eng-r{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);line-height:1.3;}
.l17-row{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:5px;margin-bottom:9px;}
.l17c{background:var(--bg3);border-radius:7px;padding:6px;text-align:center;border:1px solid var(--brd);}
.l17n{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:2px;}
.l17v{font-family:'Orbitron';font-size:14px;font-weight:700;}
.ccs-item{background:var(--bg3);border-left:2px solid var(--brd);border-radius:0 6px 6px 0;padding:5px 8px;margin-bottom:4px;font-family:'Share Tech Mono';font-size:8px;}
.tabs{display:flex;gap:4px;margin-bottom:9px;overflow-x:auto;}
.tab{padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Orbitron';font-size:8px;letter-spacing:1px;border:1px solid var(--brd);background:var(--bg3);color:var(--dim);white-space:nowrap;flex-shrink:0;}
.tab.on{border-color:var(--gold);color:var(--gold);background:rgba(240,165,0,.08);}
.tc{display:none;}.tc.on{display:block;}
.status-msg{background:rgba(41,182,246,.07);border:1px solid rgba(41,182,246,.2);border-radius:7px;padding:8px 11px;margin-bottom:9px;font-family:'Share Tech Mono';font-size:9px;color:var(--blu);display:none;}
.wsbar{position:fixed;bottom:0;left:0;right:0;z-index:200;padding:4px 12px;font-family:'Share Tech Mono';font-size:9px;background:var(--bg2);border-top:1px solid var(--brd);display:flex;align-items:center;gap:6px;}
.wsdot{width:7px;height:7px;border-radius:50%;background:var(--red);flex-shrink:0;}
.wsdot.on{background:var(--grn);animation:pulse 2s infinite;}
.auto-row{display:flex;justify-content:space-between;align-items:center;background:var(--bg2);border:1px solid var(--brd);border-radius:7px;padding:7px 11px;margin-bottom:9px;font-family:'Share Tech Mono';font-size:9px;}
.tog{width:36px;height:20px;background:var(--bg3);border-radius:10px;border:1px solid var(--brd);cursor:pointer;position:relative;display:inline-block;}
.tog.on{background:rgba(0,230,118,.2);border-color:var(--grn);}
.tog-dot{position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;background:var(--dim);transition:.2s;}
.tog.on .tog-dot{left:18px;background:var(--grn);}
.go-btn{width:100%;padding:13px;border-radius:11px;border:none;cursor:pointer;background:linear-gradient(135deg,#7a5200,var(--gold),#f5c540);color:#000;font-family:'Orbitron';font-size:11px;font-weight:900;letter-spacing:2px;box-shadow:0 6px 28px rgba(240,165,0,.3);margin-bottom:9px;}
.go-btn:disabled{background:#1a2230;color:var(--dim);box-shadow:none;}
.ki{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:6px;color:var(--grn);padding:8px;font-size:12px;font-family:'Share Tech Mono';outline:none;}
.claude-box{background:var(--bg2);border:1px solid rgba(240,165,0,.2);border-radius:11px;padding:12px;margin-bottom:9px;}
.claude-title{font-family:'Orbitron';font-size:8px;color:var(--gold);letter-spacing:1.5px;margin-bottom:8px;}
.claude-text{font-size:13px;line-height:1.9;color:var(--txt);}
</style></head>
<body>
<div class="hdr">
  <div class="logo">MATHAN AI HEMAN<small>HIGH EFFICIENCY MARKET ADAPTIVE NETWORK</small></div>
  <div style="display:flex;align-items:center;gap:8px;">
    <div class="hclock" id="clock">--:--:--</div>
    <div class="hlive off" id="live-badge">OFFLINE</div>
  </div>
</div>
<div class="sbar">
  <div><span class="sdot wait" id="sdot"></span><span id="stxt" style="color:var(--gold)">Connecting...</span></div>
  <span id="rtxt" style="color:var(--dim)">IST</span>
</div>
<div class="main">
<div class="banner">
  <div class="btitle">⚡ HEMAN</div>
  <div class="bsub">MARKET BEHAVIOUR TRADING SYSTEM</div>
  <div class="btag">CCS is BODY · AI Brain is SOUL · Live Data is BLOOD</div>
</div>
<div class="src-row none" id="src-row"><span id="src-lbl">NOT CONNECTED</span><span id="src-cnt" style="color:var(--dim)">Cycle #0</span></div>
<div class="status-msg" id="status-msg"></div>
<div class="tabs">
  <div class="tab on" onclick="ST('market',this)">📊 MARKET</div>
  <div class="tab" onclick="ST('agents',this)">🤖 AGENTS</div>
  <div class="tab" onclick="ST('engines',this)">⚙️ ENGINES</div>
  <div class="tab" onclick="ST('ccs',this)">📡 CCS</div>
  <div class="tab" onclick="ST('setup',this)">🔧 SETUP</div>
</div>

<div class="tc on" id="tc-market">
  <div class="idx-row">
    <div class="ib on" id="ib-NIFTY" onclick="setIdx('NIFTY')"><div class="ib-name">NIFTY 50</div><div class="ib-spot" id="n-spot">—</div><div class="ib-atm" id="n-atm">ATM: —</div></div>
    <div class="ib" id="ib-SENSEX" onclick="setIdx('SENSEX')"><div class="ib-name">SENSEX</div><div class="ib-spot" id="s-spot">—</div><div class="ib-atm" id="s-atm">ATM: —</div></div>
  </div>
  <div class="mstrip">
    <div class="mc"><div class="mc-n">SPOT</div><div class="mc-v" id="nv" style="color:var(--grn)">—</div><div class="mc-c" id="nc">—</div></div>
    <div class="mc"><div class="mc-n">VIX</div><div class="mc-v" id="vv" style="color:var(--gold)">—</div><div class="mc-c" id="vn">—</div></div>
    <div class="mc"><div class="mc-n">CYCLE</div><div class="mc-v" id="cyc" style="color:var(--pur)">0</div><div class="mc-c" id="ft" style="color:var(--dim)">—</div></div>
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
      <div class="pcr-marks"><span>BEAR&lt;0.8</span><span>NEUTRAL 1.0</span><span>BULL&gt;1.2</span></div>
    </div>
    <div class="sr-row">
      <div class="sr-cell sr-sup"><div class="sr-lbl" style="color:var(--grn)">SUPPORT</div><div class="sr-val" id="sup" style="color:var(--grn)">—</div><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--dim)" id="supOI">—</div></div>
      <div class="sr-cell sr-res"><div class="sr-lbl" style="color:var(--red)">RESISTANCE</div><div class="sr-val" id="res" style="color:var(--red)">—</div><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--dim)" id="resOI">—</div></div>
    </div>
  </div>
  <div class="card">
    <div class="ctitle">ATM PREMIUM</div>
    <div class="prem-grid">
      <div class="prem-cell" id="ce-cell"><div class="ptype" style="color:var(--grn)">CALL CE</div><div class="pval" id="ceVal" style="color:var(--grn)">—</div><div class="pchg" id="ceChg">—</div></div>
      <div class="prem-cell" id="pe-cell"><div class="ptype" style="color:var(--red)">PUT PE</div><div class="pval" id="peVal" style="color:var(--red)">—</div><div class="pchg" id="peChg">—</div></div>
    </div>
  </div>
  <div class="nambi-box idle" id="nambi-box">
    <div class="nambi-lbl">L14 · NAMBI MASTER CONTROLLER</div>
    <div class="nambi-sig" id="nambi-sig" style="color:var(--dim)">AWAITING DATA</div>
    <div class="nambi-conf" id="nambi-conf">Connect Angel One to begin</div>
    <div class="conf-track"><div class="conf-bull" id="conf-bull" style="width:50%"></div><div class="conf-bear" id="conf-bear" style="width:50%"></div></div>
    <div class="conf-pct"><span id="bull-pct" style="color:var(--grn)">BULL 50%</span><span id="bear-pct" style="color:var(--red)">BEAR 50%</span></div>
    <div class="reason-list" id="reason-list" style="display:none"><div class="reason-lbl">SIGNAL SOURCES</div><div id="reasons"></div></div>
  </div>
  <div class="auto-row"><span>Auto refresh 10s</span><div class="tog on" id="auto-tog" onclick="toggleAuto()"><div class="tog-dot"></div></div></div>
  <button style="width:100%;padding:9px;border-radius:9px;cursor:pointer;border:1px solid rgba(41,182,246,.4);background:rgba(41,182,246,.05);color:var(--blu);font-family:'Orbitron';font-size:9px;letter-spacing:1px;margin-bottom:9px;" onclick="doFetch()">⟳ FETCH LIVE DATA NOW</button>
</div>

<div class="tc" id="tc-agents">
  <div class="ag-sect">OI + PRICE + MACRO</div>
  <div class="ag-grid">
    <div class="agc" id="ag-l1"><div class="ag-top"><span class="ag-id">L1</span><span class="ag-sig none" id="sig-l1">—</span></div><div class="ag-name">OI Analyst</div><div class="ag-val" id="det-l1">—</div><div class="ag-conf" id="conf-l1"></div><div class="ag-w" id="w-l1"></div></div>
    <div class="agc" id="ag-l2"><div class="ag-top"><span class="ag-id">L2</span><span class="ag-sig none" id="sig-l2">—</span></div><div class="ag-name">Price Action</div><div class="ag-val" id="det-l2">—</div><div class="ag-conf" id="conf-l2"></div><div class="ag-w" id="w-l2"></div></div>
    <div class="agc" id="ag-l3"><div class="ag-top"><span class="ag-id">L3</span><span class="ag-sig none" id="sig-l3">—</span></div><div class="ag-name">VIX Monitor</div><div class="ag-val" id="det-l3">—</div><div class="ag-conf" id="conf-l3"></div><div class="ag-w" id="w-l3"></div></div>
    <div class="agc" id="ag-l4"><div class="ag-top"><span class="ag-id">L4</span><span class="ag-sig none" id="sig-l4">—</span></div><div class="ag-name">GIFT Tracker</div><div class="ag-val" id="det-l4">—</div><div class="ag-conf" id="conf-l4"></div><div class="ag-w" id="w-l4"></div></div>
  </div>
  <div class="ag-sect">PREMIUM + SESSION</div>
  <div class="ag-grid">
    <div class="agc" id="ag-l5"><div class="ag-top"><span class="ag-id">L5</span><span class="ag-sig none" id="sig-l5">—</span></div><div class="ag-name">CE Premium</div><div class="ag-val" id="det-l5">—</div><div class="ag-conf" id="conf-l5"></div><div class="ag-w" id="w-l5"></div></div>
    <div class="agc" id="ag-l6"><div class="ag-top"><span class="ag-id">L6</span><span class="ag-sig none" id="sig-l6">—</span></div><div class="ag-name">PE Premium</div><div class="ag-val" id="det-l6">—</div><div class="ag-conf" id="conf-l6"></div><div class="ag-w" id="w-l6"></div></div>
    <div class="agc" id="ag-l7"><div class="ag-top"><span class="ag-id">L7</span><span class="ag-sig none" id="sig-l7">—</span></div><div class="ag-name">Session Clock</div><div class="ag-val" id="det-l7">—</div><div class="ag-conf" id="conf-l7"></div><div class="ag-w" id="w-l7"></div></div>
    <div class="agc" id="ag-l8"><div class="ag-top"><span class="ag-id">L8</span><span class="ag-sig none" id="sig-l8">—</span></div><div class="ag-name">Expiry Watcher</div><div class="ag-val" id="det-l8">—</div><div class="ag-conf" id="conf-l8"></div><div class="ag-w" id="w-l8"></div></div>
  </div>
  <div class="ag-sect">BEHAVIOUR + INTELLIGENCE</div>
  <div class="ag-grid">
    <div class="agc" id="ag-l9"><div class="ag-top"><span class="ag-id">L9</span><span class="ag-sig none" id="sig-l9">—</span></div><div class="ag-name">Gap Detector</div><div class="ag-val" id="det-l9">—</div><div class="ag-conf" id="conf-l9"></div><div class="ag-w" id="w-l9"></div></div>
    <div class="agc" id="ag-l10"><div class="ag-top"><span class="ag-id">L10</span><span class="ag-sig none" id="sig-l10">—</span></div><div class="ag-name">PCR Engine</div><div class="ag-val" id="det-l10">—</div><div class="ag-conf" id="conf-l10"></div><div class="ag-w" id="w-l10"></div></div>
    <div class="agc" id="ag-l11"><div class="ag-top"><span class="ag-id">L11</span><span class="ag-sig none" id="sig-l11">—</span></div><div class="ag-name">Trap Detector</div><div class="ag-val" id="det-l11">—</div><div class="ag-conf" id="conf-l11"></div><div class="ag-w" id="w-l11"></div></div>
    <div class="agc" id="ag-l12"><div class="ag-top"><span class="ag-id">L12</span><span class="ag-sig none" id="sig-l12">—</span></div><div class="ag-name">Risk Control</div><div class="ag-val" id="det-l12">—</div><div class="ag-conf" id="conf-l12"></div><div class="ag-w" id="w-l12"></div></div>
  </div>
  <div class="ag-sect">L13 · MASTER BEHAVIOUR AI</div>
  <div class="agc" id="ag-l13" style="padding:10px;margin-bottom:9px;">
    <div class="ag-top"><span class="ag-id" style="font-size:9px">L13</span><span class="ag-sig none" id="sig-l13" style="font-size:12px">—</span></div>
    <div class="ag-name" style="font-size:12px;margin-bottom:4px">Behaviour AI</div>
    <div class="ag-val" id="det-l13">—</div><div class="ag-conf" id="conf-l13"></div><div class="ag-w" id="w-l13"></div>
  </div>
  <div class="card">
    <div class="ctitle">L17 · SELF LEARNING ENGINE</div>
    <div class="l17-row">
      <div class="l17c"><div class="l17n">TRADES</div><div class="l17v" id="l17t" style="color:var(--gold)">0</div></div>
      <div class="l17c"><div class="l17n">WINS</div><div class="l17v" id="l17w" style="color:var(--grn)">0</div></div>
      <div class="l17c"><div class="l17n">LOSS</div><div class="l17v" id="l17l" style="color:var(--red)">0</div></div>
      <div class="l17c"><div class="l17n">WIN%</div><div class="l17v" id="l17r" style="color:var(--blu)">0%</div></div>
    </div>
  </div>
</div>

<div class="tc" id="tc-engines">
  <div class="eng-row">
    <div class="eng-cell"><div class="eng-lbl">L15 · TRUTH ENGINE</div><div class="eng-val" id="l15v" style="color:var(--dim)">—</div><div class="eng-r" id="l15r">Awaiting</div><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--blu);margin-top:3px" id="l15c"></div></div>
    <div class="eng-cell"><div class="eng-lbl">L16 · CONTRADICTION</div><div class="eng-val" id="l16v" style="color:var(--dim)">—</div><div class="eng-r" id="l16a">Awaiting</div><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--blu);margin-top:3px" id="l16c"></div></div>
  </div>
  <div class="card"><div class="ctitle">L16 DETAIL</div><div style="font-family:'Share Tech Mono';font-size:9px;color:var(--txt);line-height:1.6" id="l16d">—</div></div>
  <div class="card">
    <div class="ctitle">SYSTEM STATUS</div>
    <div style="font-family:'Share Tech Mono';font-size:9px;line-height:1.8">
      <div>Angel: <span id="sys-angel" style="color:var(--dim)">—</span></div>
      <div>WebSocket: <span id="sys-ws" style="color:var(--dim)">—</span></div>
      <div>Source: <span id="sys-src" style="color:var(--dim)">—</span></div>
      <div>Last fetch: <span id="sys-ft" style="color:var(--dim)">—</span></div>
    </div>
  </div>
</div>

<div class="tc" id="tc-ccs">
  <div class="card">
    <div class="ctitle">CCS · COMMAND CONTROL SYSTEM
      <button onclick="wsSend({type:'get_ccs_log'})" style="padding:3px 8px;border-radius:4px;cursor:pointer;border:1px solid var(--brd);background:var(--bg3);color:var(--dim);font-family:'Share Tech Mono';font-size:7px">REFRESH</button>
    </div>
    <div id="ccs-log" style="max-height:400px;overflow-y:auto"></div>
  </div>
</div>

<div class="tc" id="tc-setup">
  <div class="card" style="border-color:rgba(206,147,216,.3)">
    <div class="ctitle" style="color:var(--pur)">ANGEL ONE <span id="angel-st" style="font-family:'Share Tech Mono';font-size:8px;color:var(--dim)">NOT SET</span></div>
    <div style="font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:8px">Saved in DB. Auto-loads on restart.</div>
    <div class="inp-lbl">API KEY</div><input class="inp" id="api-key" type="password" placeholder="API Key"/>
    <div class="inp-lbl">CLIENT ID</div><input class="inp" id="client-id" type="text" placeholder="A12345"/>
    <div class="inp-lbl">PIN</div><input class="inp" id="angel-pin" type="password" placeholder="1234"/>
    <div class="inp-lbl">TOTP SECRET</div><input class="inp" id="totp-secret" type="password" placeholder="JBSWY3DPEHPK3PXP"/>
    <button class="cbtn pur" onclick="connectAngel()">CONNECT ANGEL ONE</button>
  </div>
  <div class="card" style="border-color:rgba(41,182,246,.2)">
    <div class="ctitle" style="color:var(--blu)">TELEGRAM <span id="tg-st" style="font-family:'Share Tech Mono';font-size:8px;color:var(--dim)">OFF</span></div>
    <div class="inp-lbl">BOT TOKEN</div><input class="inp" id="tg-token" type="password" placeholder="1234567890:AAB..."/>
    <div class="inp-lbl">CHAT ID</div><input class="inp" id="tg-chat" type="text" placeholder="-100123456789"/>
    <button class="cbtn" onclick="saveTG()">SAVE & TEST</button>
  </div>
  <div class="card">
    <div class="ctitle">CAPITAL</div>
    <div class="inp-lbl">TRADING CAPITAL (₹)</div>
    <input class="inp" id="cap-inp" type="number" placeholder="10000" value="10000"/>
    <button class="cbtn grn" onclick="saveCap()">SAVE</button>
  </div>
  <div class="card" style="border-color:rgba(240,165,0,.2)">
    <div class="ctitle" style="color:var(--gold)">CLAUDE AI KEY</div>
    <input class="ki" id="ki" type="password" placeholder="sk-ant-..." oninput="saveKey()"/>
    <div id="kst" style="font-family:'Share Tech Mono';font-size:9px;margin-top:3px"></div>
  </div>
  <div style="display:flex;gap:7px;margin-bottom:9px">
    <input style="flex:1;background:var(--bg3);border:1px solid var(--brd);border-radius:7px;color:var(--txt);padding:9px;font-size:14px;font-family:'Share Tech Mono';outline:none" id="cap" type="number" placeholder="Capital ₹" value="10000"/>
    <button style="padding:9px 14px;border-radius:7px;cursor:pointer;border:1px solid var(--gold);background:rgba(240,165,0,.08);color:var(--gold);font-family:'Orbitron';font-size:8px;font-weight:700" onclick="runTrade()">PLAN</button>
  </div>
  <button class="go-btn" id="go-btn" onclick="runClaude()">⚡ NAMBI + CLAUDE — FULL STRATEGY</button>
  <div class="claude-box" id="claude-box" style="display:none"><div class="claude-title">CLAUDE AI — HEMAN STRATEGY</div><div class="claude-text" id="claude-text"></div></div>
</div>
</div>

<div class="wsbar"><div class="wsdot" id="wsdot"></div><span id="ws-txt">Connecting...</span><span id="ws-info" style="margin-left:auto;color:var(--dim)"></span></div>

<script>
const WS_URL=location.origin.replace(/^http/,'ws')+'/ws';
let ws=null,ok=false,rcD=1000,rcT=null,hbT=null,wdT=null,hbM=0,conn=false,autoOn=true,SS={};

function ST(id,el){
  document.querySelectorAll('.tc').forEach(e=>e.className='tc');
  document.querySelectorAll('.tab').forEach(e=>e.className='tab');
  document.getElementById('tc-'+id).className='tc on';
  el.className='tab on';
}
function son(){ok=true;hbM=0;rcD=1000;conn=false;q('wsdot').className='wsdot on';q('live-badge').className='hlive on';q('live-badge').textContent='LIVE';wst('Connected');}
function soff(r){ok=false;q('wsdot').className='wsdot';q('live-badge').className='hlive off';q('live-badge').textContent='OFFLINE';wst(r||'Offline');}
function stT(){clearInterval(hbT);hbT=null;clearInterval(wdT);wdT=null;clearTimeout(rcT);rcT=null;}
function sC(){if(!ws)return;try{ws.onopen=ws.onmessage=ws.onerror=ws.onclose=null;if(ws.readyState<=1)ws.close();}catch(e){}ws=null;}
function schedRC(){if(rcT)return;soff('Reconnecting '+Math.round(rcD/1000)+'s...');rcT=setTimeout(()=>{rcT=null;connect();rcD=Math.min(rcD*2,10000);},rcD);}
function startHB(){stT();hbM=0;
  hbT=setInterval(()=>{if(!ws||ws.readyState!==1){stT();schedRC();return;}ws.send(JSON.stringify({type:'ping'}));hbM++;if(hbM>=3){stT();sC();schedRC();}},3000);
  wdT=setInterval(()=>{if(!ws||ws.readyState!==1){stT();sC();schedRC();}},5000);}
function connect(){
  if(conn)return;if(ws&&ws.readyState===1)return;
  conn=true;sC();wst('Connecting...');
  try{ws=new WebSocket(WS_URL);}catch(e){conn=false;schedRC();return;}
  const ot=setTimeout(()=>{if(!ws||ws.readyState!==1){conn=false;sC();schedRC();}},8000);
  ws.onopen=()=>{clearTimeout(ot);son();startHB();try{ws.send(JSON.stringify({type:'get_state'}));}catch(e){}};
  ws.onmessage=(e)=>{hbM=0;let m;try{m=JSON.parse(e.data);}catch{return;}handle(m);};
  ws.onerror=()=>{clearTimeout(ot);conn=false;stT();sC();schedRC();};
  ws.onclose=(e)=>{clearTimeout(ot);conn=false;stT();soff('DC('+e.code+')');schedRC();};}
function wsSend(o){
  if(ws&&ws.readyState===1){ws.send(JSON.stringify(o));return;}
  if(o.type==='connect_angel'){fetch('/connect_angel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)}).catch(()=>{});}
}

function handle(m){
  const t=m.type;
  if(t==='pong')return;
  if(t==='heartbeat'){
    t_('sys-angel',m.angel?'✅ Connected':'❌ Not connected');
    t_('sys-ws',m.ws?'✅ Live':'❌ Stopped');
    t_('cyc',m.count||0);return;}
  if(t==='full_state'){applyState(m.state);return;}
  if(t==='nambi_update'){applyNambi(m.nambi);return;}
  if(t==='angel_ok'){showMsg('✅ Angel One: '+m.client,'grn');t_('angel-st','✅ '+m.client);return;}
  if(t==='angel_err'){showMsg('❌ '+m.msg,'red');return;}
  if(t==='angel_ws_connected'){showMsg('✅ WebSocket live — OI streaming','grn');t_('oi-badge','LIVE');q('oi-badge').className='badge live';return;}
  if(t==='angel_ws_error'){showMsg('⚠️ WS error: '+m.error,'orn');return;}
  if(t==='status_msg'){showMsg(m.msg,'blu');return;}
  if(t==='tg_ok'){t_('tg-st','✅ ON');showMsg('Telegram connected!','grn');return;}
  if(t==='ccs_event'){appendCCS(m.event);return;}
  if(t==='ccs_history'){renderCCS(m.events);return;}
}

function applyState(s){
  if(!s)return;SS=s;
  const mk=s.market||{};const sys=s.sys||{};
  const sp=mk.spot,atm=mk.atm,pcr=mk.pcr;
  t_('nv',sp?sp.toFixed(0):'—');t_('n-spot',sp?sp.toFixed(0):'—');
  t_('n-atm',atm?'ATM:'+atm:'ATM:—');t_('s-spot',sp?sp.toFixed(0):'—');
  t_('vv',mk.vix?mk.vix.toFixed(1):'—');
  t_('callOI',fmtOI(mk.call_oi));t_('putOI',fmtOI(mk.put_oi));
  t_('sup',mk.support||'—');t_('res',mk.resistance||'—');
  t_('supOI',fmtOI(mk.sup_oi));t_('resOI',fmtOI(mk.res_oi));
  if(pcr){
    t_('pcrVal',pcr.toFixed(2));
    const fill=Math.min(100,Math.max(0,(pcr-0.5)/1.5*100));
    q('pcrFill').style.width=fill+'%';
    q('pcrFill').style.background=pcr>1.2?'var(--grn)':pcr<0.8?'var(--red)':'var(--gold)';
  }
  const ce=mk.ce_prem,pe=mk.pe_prem,cep=mk.ce_prev,pep=mk.pe_prev;
  t_('ceVal',ce?'₹'+ce.toFixed(0):'—');t_('peVal',pe?'₹'+pe.toFixed(0):'—');
  if(ce&&cep){const c=ce-cep;t_('ceChg',(c>=0?'+':'')+c.toFixed(1));q('ceChg').style.color=c>0?'var(--grn)':'var(--red)';}
  if(pe&&pep){const c=pe-pep;t_('peChg',(c>=0?'+':'')+c.toFixed(1));q('peChg').style.color=c>0?'var(--red)':'var(--grn)';}
  t_('cyc',sys.count||0);t_('ft',mk.fetch_time||'—');
  t_('sys-src',sys.source||'—');t_('sys-ft',mk.fetch_time||'—');
  t_('src-cnt','Cycle #'+(sys.count||0));
  updateSrc(sys.source||'NONE');
  const ags=s.agents||{};
  for(const [id,ag] of Object.entries(ags))updateAgent(id,ag);
  if(s.nambi)applyNambi(s.nambi);
  const l15=s.l15||{};const vc=l15.verdict;
  t_('l15v',vc||'—');
  q('l15v').style.color=vc==='TRUE_MOVE'?'var(--grn)':vc==='FAKE_MOVE'?'var(--red)':vc==='TRAP'?'var(--orn)':'var(--dim)';
  t_('l15r',l15.reason||'—');t_('l15c',l15.confidence?l15.confidence+'%':'');
  const l16=s.l16||{};const ts=l16.trap_status;
  t_('l16v',ts||'—');
  q('l16v').style.color=(ts==='CALL_TRAP'||ts==='PUT_TRAP')?'var(--red)':ts==='TRUE_MOVE'?'var(--grn)':'var(--dim)';
  t_('l16a',l16.action||'—');t_('l16d',l16.reason||'—');t_('l16c',l16.confidence?l16.confidence+'%':'');
  const l17=s.l17||{};
  t_('l17t',l17.total_trades||0);t_('l17w',l17.wins||0);t_('l17l',l17.losses||0);t_('l17r',(l17.win_rate||0)+'%');
  const ang=s.angel||{};
  if(ang.connected)t_('angel-st','✅ '+ang.client_id);
  if(s.telegram&&s.telegram.enabled)t_('tg-st','✅ ON');
}

function updateAgent(id,ag){
  const sig=ag.signal||'none';
  const el=q('ag-'+id);
  if(el)el.className='agc '+(sig==='bull'?'bull':sig==='bear'?'bear':sig==='hold'?'hold':'');
  const sc=q('sig-'+id);
  if(sc){sc.textContent=sig==='bull'?'BULL':sig==='bear'?'BEAR':sig==='hold'?'HOLD':'—';sc.className='ag-sig '+(sig||'none');}
  t_('det-'+id,ag.detail||'—');
  t_('conf-'+id,ag.confidence?'Conf:'+ag.confidence+'%':'');
  t_('w-'+id,ag.weight?'W:'+ag.weight.toFixed(1):'');
}

function applyNambi(n){
  if(!n)return;
  const sig=n.signal||'WAIT';
  const box=q('nambi-box');
  box.className='nambi-box '+(sig==='BUY CE'?'buy-ce':sig==='BUY PE'?'buy-pe':sig==='WAIT'?'wait':'idle');
  const sc=q('nambi-sig');
  sc.textContent=sig;
  sc.style.color=sig==='BUY CE'?'var(--grn)':sig==='BUY PE'?'var(--red)':'var(--gold)';
  t_('nambi-conf',n.confidence+' CONFIDENCE'+(n.trap_detected?' | ⚠️ TRAP':'')+(n.conflict?' | ⚡ CONFLICT':''));
  q('conf-bull').style.width=(n.bull_pct||50)+'%';
  q('conf-bear').style.width=(n.bear_pct||50)+'%';
  t_('bull-pct','BULL '+(n.bull_pct||50)+'%');
  t_('bear-pct','BEAR '+(n.bear_pct||50)+'%');
  const rl=q('reason-list');
  if(n.reasons&&n.reasons.length){
    rl.style.display='block';
    q('reasons').innerHTML=n.reasons.map(r=>'<div class="reason-item">'+r+'</div>').join('');
  }else rl.style.display='none';
}

function updateSrc(src){
  const row=q('src-row');
  if(src==='ANGEL ONE'){
    row.className='src-row live';t_('src-lbl','✅ ANGEL ONE LIVE');
    q('sdot').className='sdot ok';q('stxt').textContent='Angel One live';q('stxt').style.color='var(--grn)';
  }else{
    row.className='src-row none';t_('src-lbl','NOT CONNECTED');
    q('sdot').className='sdot wait';q('stxt').textContent='Waiting...';q('stxt').style.color='var(--gold)';
  }
}

function appendCCS(ev){
  const el=document.createElement('div');
  const cls=ev.type||'';
  el.className='ccs-item '+cls;
  el.style.borderLeftColor=cls.includes('DECISION')?'var(--blu)':cls.includes('RESULT')?'var(--pur)':cls.includes('CONNECTED')||cls.includes('LOGIN')?'var(--grn)':'var(--gold)';
  el.innerHTML='<span style="color:var(--dim);margin-right:6px">'+ev.ts+'</span><span style="color:var(--orn);margin-right:4px">'+ev.source+'→'+ev.target+'</span><span>'+ev.message+'</span>';
  const log=q('ccs-log');log.prepend(el);
  if(log.children.length>80)log.lastChild.remove();
}
function renderCCS(evs){q('ccs-log').innerHTML='';evs.slice().reverse().forEach(ev=>appendCCS(ev));}

function connectAngel(){
  const ak=q('api-key').value.trim(),ci=q('client-id').value.trim(),
        pin=q('angel-pin').value.trim(),ts=q('totp-secret').value.trim();
  if(!ak||!ci||!pin||!ts){showMsg('All 4 fields required','red');return;}
  showMsg('Connecting...','blu');
  wsSend({type:'connect_angel',api_key:ak,client_id:ci,pin:pin,totp_secret:ts});
  localStorage.setItem('a_ak',ak);localStorage.setItem('a_ci',ci);
  localStorage.setItem('a_pin',pin);localStorage.setItem('a_ts',ts);
}
function setIdx(i){
  wsSend({type:'set_index',index:i});
  ['NIFTY','SENSEX'].forEach(n=>q('ib-'+n).className='ib'+(n===i?' on':''));
}
function doFetch(){wsSend({type:'fetch'});}
function toggleAuto(){autoOn=!autoOn;wsSend({type:'set_auto',on:autoOn});q('auto-tog').className='tog'+(autoOn?' on':'');}
function saveTG(){
  const tt=q('tg-token').value.trim(),tc=q('tg-chat').value.trim();
  if(!tt||!tc){showMsg('Token & Chat ID required','red');return;}
  wsSend({type:'set_telegram',token:tt,chat_id:tc});
}
function saveCap(){
  const cap=parseFloat(q('cap-inp').value||10000);
  wsSend({type:'set_capital',capital:cap});showMsg('Capital saved ₹'+cap,'grn');
}
function saveKey(){const k=q('ki').value.trim();if(k){localStorage.setItem('mbk',k);t_('kst','✅ Saved');}}
function loadSaved(){
  const k=localStorage.getItem('mbk');if(k){q('ki').value=k;t_('kst','✅ Loaded');}
  const ak=localStorage.getItem('a_ak');if(ak)q('api-key').value=ak;
  const ci=localStorage.getItem('a_ci');if(ci)q('client-id').value=ci;
  const pin=localStorage.getItem('a_pin');if(pin)q('angel-pin').value=pin;
  const ts=localStorage.getItem('a_ts');if(ts)q('totp-secret').value=ts;
}

async function runClaude(){
  const key=localStorage.getItem('mbk');
  if(!key){alert('Setup tab-ல் Claude API Key enter பண்ணுங்க');return;}
  const btn=q('go-btn');btn.disabled=true;btn.textContent='Analysing...';
  q('claude-box').style.display='block';
  const ct=q('claude-text');ct.textContent='HEMAN analysing...';
  const s=SS;const mk=s.market||{};const nb=s.nambi||{};const l16=s.l16||{};const l15=s.l15||{};
  const prompt=`You are Nambi from Mathan AI HEMAN — Behaviour Intelligence Trading Engine.

LIVE DATA:
Index:${s.sys?.index||'NIFTY'} Spot:${mk.spot?.toFixed(0)||'—'} ATM:${mk.atm||'—'}
VIX:${mk.vix?.toFixed(1)||'—'} PCR:${mk.pcr?.toFixed(2)||'—'}
Call OI:${mk.call_oi||'—'} Put OI:${mk.put_oi||'—'}
CE:₹${mk.ce_prem?.toFixed(0)||'—'} PE:₹${mk.pe_prem?.toFixed(0)||'—'}
Support:${mk.support||'—'} Resistance:${mk.resistance||'—'}

NAMBI: ${nb.signal||'WAIT'} | ${nb.confidence||'—'} | Bull:${nb.bull_pct||50}% Bear:${nb.bear_pct||50}%
L15 Truth: ${l15.verdict||'—'} — ${l15.reason||'—'}
L16 Contradiction: ${l16.trap_status||'—'} → ${l16.action||'—'}

Capital:₹${q('cap').value||10000}

Give precise strategy: Entry strike, Premium, SL, Target, Lots. Max 150 words. Direct.`;
  try{
    const resp=await fetch('https://api.anthropic.com/v1/messages',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({model:'claude-sonnet-4-20250514',max_tokens:1000,messages:[{role:'user',content:prompt}]})
    });
    const data=await resp.json();
    const txt=data.content?.map(i=>i.text||'').join('')||'No response';
    ct.innerHTML=txt.replace(/\n/g,'<br>');
  }catch(e){ct.textContent='Error:'+e.message;}
  btn.disabled=false;btn.textContent='⚡ NAMBI + CLAUDE — FULL STRATEGY';
}

function runTrade(){
  const s=SS;const mk=s.market||{};const nb=s.nambi||{};
  const cap=parseFloat(q('cap').value||10000);
  const sig=nb.signal||'WAIT';
  q('claude-box').style.display='block';
  const ct=q('claude-text');
  if(sig==='WAIT'){ct.textContent='NAMBI says WAIT — No trade now.';return;}
  const lot=s.sys?.index==='NIFTY'?75:20;
  const price=sig==='BUY CE'?mk.ce_prem:mk.pe_prem;
  if(!price){ct.textContent='Premium not available.';return;}
  const lots=Math.max(1,Math.floor(cap/(price*lot)));
  const sl=(price*0.35).toFixed(0);const tgt=(price*1.6).toFixed(0);
  ct.innerHTML=`<b>${sig}</b> — ATM ${mk.atm}<br>Premium:₹${price.toFixed(0)}<br>Lots:${lots} (₹${(lots*lot*price).toFixed(0)} margin)<br>SL:₹${sl} | Target:₹${tgt}<br>Risk:₹${(lots*lot*(price-sl)).toFixed(0)} | Reward:₹${(lots*lot*(tgt-price)).toFixed(0)}`;
}

function q(i){return document.getElementById(i);}
function t_(i,v){const e=q(i);if(e)e.textContent=v;}
function fmtOI(n){if(!n)return'—';if(n>10000000)return(n/10000000).toFixed(1)+'Cr';if(n>100000)return(n/100000).toFixed(1)+'L';if(n>1000)return(n/1000).toFixed(1)+'K';return''+n;}
function wst(t){q('ws-txt').textContent=t;}
function showMsg(msg,col){
  const d=q('status-msg');d.style.display='block';d.textContent=msg;
  const cols={grn:'var(--grn)',red:'var(--red)',blu:'var(--blu)',orn:'var(--orn)'};
  d.style.color=cols[col]||'var(--blu)';
  setTimeout(()=>{d.style.display='none';},5000);
}
setInterval(()=>{
  const n=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Kolkata'}));
  const p=v=>String(v).padStart(2,'0');
  const ts=p(n.getHours())+':'+p(n.getMinutes())+':'+p(n.getSeconds());
  t_('clock',ts);t_('rtxt','IST '+ts);
},1000);
window.onload=()=>{loadSaved();connect();};
</script>
</body>
</html>"""

# ── STARTUP ──────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("╔══════════════════════════════════════╗")
    log.info("║   MATHAN AI HEMAN — STARTING        ║")
    log.info("║   High Efficiency Market Adaptive   ║")
    log.info("╚══════════════════════════════════════╝")
    db_init()
    db_load()
    l17_load()
    if all([ANGEL["api_key"],ANGEL["client_id"],ANGEL["pin"],ANGEL["totp_secret"]]):
        log.info("[STARTUP] Credentials found — auto-connecting Angel One...")
        threading.Thread(
            target=do_angel_connect,
            args=(ANGEL["api_key"],ANGEL["client_id"],ANGEL["pin"],ANGEL["totp_secret"]),
            daemon=True
        ).start()
    else:
        log.info("[STARTUP] No credentials — waiting for user login via dashboard")
    threading.Thread(target=push_loop,daemon=True).start()
    threading.Thread(target=poll_loop,daemon=True).start()
    ip=local_ip()
    log.info(f"OPEN: http://{ip}:{PORT}")
    log.info(f"PING: http://{ip}:{PORT}/ping")
    app.run(host="0.0.0.0",port=PORT,use_reloader=False,threaded=True)
