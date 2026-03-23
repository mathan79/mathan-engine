"""
MATHAN AI HEMAN
High Efficiency Market Adaptive Network
========================================
CCS is BODY | AI Brain is SOUL | Live Data is BLOOD
From Behaviour to Decision | From Decision to Execution | From Execution to Intelligence

Layers: L1-L13 Agents + L14 NAMBI + L15 Truth + L16 Contradiction + L17 Learning
"""
import os,json,time,threading,datetime,requests,pyotp,logging
from flask import Flask,Response,jsonify,request
from flask_cors import CORS

logging.basicConfig(level=logging.INFO,format="%(asctime)s [HEMAN] %(message)s")
log = logging.getLogger("HEMAN")

app  = Flask(__name__)
CORS(app)
PORT = int(os.environ.get("PORT",8000))

# ── SMARTAPI OPTIONAL ──────────────────────────────────────────────────
try:
    from SmartApi import SmartConnect
    SMARTAPI_OK = True
except ImportError:
    SMARTAPI_OK = False
    log.warning("SmartAPI not installed — Angel One disabled")

# ── CREDENTIALS ───────────────────────────────────────────────────────
ANGEL = {
    "api_key":     os.environ.get("ANGEL_API_KEY",    "jYAKgdt3"),
    "client_id":   os.environ.get("ANGEL_CLIENT_ID",  "V542909"),
    "pin":         os.environ.get("ANGEL_PIN",        "1818"),
    "totp_secret": os.environ.get("ANGEL_TOTP",       "KJ4MRMUWNTFTCUALRBH5ALKA7A"),
    "connected":   False, "jwt_token": "", "error": None,
}
TELEGRAM = {
    "token": os.environ.get("TELEGRAM_TOKEN",""),
    "chat_id": os.environ.get("TELEGRAM_CHAT_ID",""),
}

INDEX_CFG = {
    "NIFTY":  {"step":50,  "lot":65, "expiry_dow":1},
    "SENSEX": {"step":100, "lot":20, "expiry_dow":3},
}

# ── STATE ─────────────────────────────────────────────────────────────
M = {
    "nifty":None,"sensex":None,"vix":None,"gift":None,"gift_diff":None,
    "atm":None,"gap":None,"pcr":None,"call_oi":None,"put_oi":None,
    "ce_prem":None,"pe_prem":None,"ce_prev":None,"pe_prev":None,
    "support":None,"resistance":None,"exp_days":None,
    "source":"LOADING","fetch_time":None,"market_status":"CHECKING",
}

# L17 Self-Learning weights (start equal)
WEIGHTS = {
    "l1":1.5,"l2":1.5,"l3":1.5,"l4":1.0,"l5":1.0,
    "l6":1.0,"l7":0.8,"l8":0.8,"l9":1.0,"l10":1.2,
    "l11":1.5,"l12":1.2,"l13":2.0,"l14":3.0,
}

AGENTS = {f"l{i}":{"signal":None,"detail":"","confidence":0} for i in range(1,15)}

BRAIN = {
    "signal":"WAIT","bull_pct":50,"bear_pct":50,"confidence":"LOW",
    "reasons":[],"trap":False,"nambi_verdict":"STANDBY","nambi_reason":"",
    "truth":"UNKNOWN","contradiction":"NONE","learning_note":"",
}

SYS = {
    "count":0,"error":None,"index":"NIFTY","angel_ok":False,
    "market_status":"CHECKING","keep_alive_count":0,
    "trade_log":[],"daily_pnl":0,"win_count":0,"loss_count":0,
}

LOCK = threading.Lock()

# ── HELPERS ───────────────────────────────────────────────────────────
def ist():
    tz=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
    return datetime.datetime.now(tz).strftime("%H:%M:%S")

def ist_now():
    tz=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
    return datetime.datetime.now(tz)

def ist_mins():
    n=ist_now(); return n.hour*60+n.minute

def calc_expiry(index="NIFTY"):
    tz=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
    t=datetime.datetime.now(tz)
    dow=INDEX_CFG[index]["expiry_dow"]
    d2t=(dow-t.weekday())%7
    if d2t==0 and t.hour>=15 and t.minute>=30: d2t=7
    return d2t

def market_status():
    n=ist_now()
    days=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    mins=n.hour*60+n.minute
    if n.weekday()>=5: return f"MARKET CLOSED — {days[n.weekday()]} Weekend",False
    if mins<9*60+15:   return "PRE-MARKET — Opens 9:15 AM",False
    if mins>15*60+30:  return "MARKET CLOSED — After 3:30 PM",False
    return "MARKET OPEN",True

NSE_HDR={"User-Agent":"Mozilla/5.0","Accept":"*/*","Referer":"https://www.nseindia.com/option-chain"}

# ── DATA FETCH ────────────────────────────────────────────────────────
def fetch_yahoo_all():
    hdrs={"User-Agent":"Mozilla/5.0"}
    tickers={"nifty":"%5ENSEI","sensex":"%5EBSESN","vix":"%5EINDIAVIX","gift":"NIFTYFUTURES.NS"}
    for key,sym in tickers.items():
        try:
            r=requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                params={"interval":"1d","range":"5d"},headers=hdrs,timeout=10)
            meta=r.json()["chart"]["result"][0]["meta"]
            sp=meta.get("regularMarketPrice",0) or meta.get("previousClose",0)
            if not sp: continue
            with LOCK:
                if key=="nifty":
                    M["nifty"]=sp
                    M["atm"]=round(sp/50)*50
                    M["gap"]=round(sp-(meta.get("previousClose",sp)),2)
                elif key=="sensex": M["sensex"]=sp
                elif key=="vix":    M["vix"]=sp
                elif key=="gift":
                    M["gift"]=sp
                    if M["nifty"]: M["gift_diff"]=round(sp-M["nifty"],2)
        except Exception as e:
            log.debug(f"Yahoo {key}: {e}")

def fetch_nse_oi(index="NIFTY"):
    try:
        s=requests.Session()
        s.get("https://www.nseindia.com",headers={**NSE_HDR,"Accept":"text/html"},timeout=7)
        time.sleep(0.3)
        r=s.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={index}",
                headers=NSE_HDR,timeout=12)
        if r.status_code!=200: return False
        raw=r.json().get("records",{})
        spot=raw.get("underlyingValue",0)
        data=raw.get("data",[]); exps=raw.get("expiryDates",[])
        if not spot or not data: return False
        target=exps[0] if exps else ""
        cfg=INDEX_CFG[index]; atm=round(spot/cfg["step"])*cfg["step"]
        tC=tP=mxC=mxP=mxCS=mxPS=ceLTP=peLTP=0
        for row in data:
            if target and row.get("expiryDate","")!=target: continue
            st=row.get("strikePrice",0)
            ce=row.get("CE",{}); pe=row.get("PE",{})
            ceOI=ce.get("openInterest",0) or 0
            peOI=pe.get("openInterest",0) or 0
            ceLtp=ce.get("lastPrice",0) or 0
            peLtp=pe.get("lastPrice",0) or 0
            tC+=ceOI; tP+=peOI
            if ceOI>mxC: mxC=ceOI; mxCS=st
            if peOI>mxP: mxP=peOI; mxPS=st
            if abs(st-atm)<=cfg["step"]:
                if ceLtp: ceLTP=ceLtp
                if peLtp: peLTP=peLtp
        if tC==0: return False
        with LOCK:
            M["nifty"]=spot; M["atm"]=atm
            M["ce_prev"]=M["ce_prem"]; M["pe_prev"]=M["pe_prem"]
            M["call_oi"]=tC; M["put_oi"]=tP
            M["pcr"]=round(tP/tC,2)
            M["ce_prem"]=ceLTP; M["pe_prem"]=peLTP
            M["support"]=mxPS; M["resistance"]=mxCS
            M["source"]="NSE REAL OI ✓"
            M["exp_days"]=calc_expiry(index)
            M["fetch_time"]=ist()
            SYS["count"]+=1; SYS["error"]=None
        log.info(f"NSE OI: spot={spot} pcr={round(tP/tC,2)} CE={ceLTP} PE={peLTP}")
        return True
    except Exception as e:
        log.error(f"NSE: {e}"); return False

def estimate_oi():
    with LOCK:
        sp=M["nifty"] or 23000
        idx=SYS["index"]; cfg=INDEX_CFG[idx]
        atm=round(sp/cfg["step"])*cfg["step"]
        base=sp*180
        M["atm"]=atm; M["call_oi"]=int(base); M["put_oi"]=int(base*1.08)
        M["pcr"]=1.08; M["support"]=atm-cfg["step"]*2; M["resistance"]=atm+cfg["step"]*2
        M["ce_prem"]=round(sp*0.004); M["pe_prem"]=round(sp*0.0037)
        M["exp_days"]=calc_expiry(idx); M["source"]="ESTIMATED"
        M["fetch_time"]=ist()

# ── L1-L13 AGENTS ─────────────────────────────────────────────────────
def run_agents_l1_l13(snap,sys_snap):
    spot=snap.get("nifty"); vix=snap.get("vix"); pcr=snap.get("pcr")
    atm=snap.get("atm"); gd=snap.get("gift_diff")
    ce=snap.get("ce_prem"); pe=snap.get("pe_prem")
    ce_p=snap.get("ce_prev"); pe_p=snap.get("pe_prev")
    sup=snap.get("support"); res=snap.get("resistance")
    exp=snap.get("exp_days"); gap=snap.get("gap")
    ms=snap.get("market_status",""); mins=ist_mins()
    ag={}

    # L1 OI Analyst
    if pcr:
        if pcr>1.5:   ag["l1"]=("bull",f"PCR {pcr} STRONG BULL",85)
        elif pcr>1.2: ag["l1"]=("bull",f"PCR {pcr} BULLISH",70)
        elif pcr<0.6: ag["l1"]=("bear",f"PCR {pcr} STRONG BEAR",85)
        elif pcr<0.8: ag["l1"]=("bear",f"PCR {pcr} BEARISH",70)
        else:         ag["l1"]=("neut",f"PCR {pcr} NEUTRAL",50)
    else: ag["l1"]=("neut","PCR N/A",0)

    # L2 Price Action
    if spot and atm:
        if res and spot>res:       ag["l2"]=("bull",f"BREAKOUT {int(res)}",80)
        elif sup and spot<sup:     ag["l2"]=("bear",f"BREAKDOWN {int(sup)}",80)
        elif spot>atm+50:          ag["l2"]=("bull",f"Above ATM {atm}",65)
        elif spot<atm-50:          ag["l2"]=("bear",f"Below ATM {atm}",65)
        else:                      ag["l2"]=("neut",f"At ATM {atm}",50)
    else: ag["l2"]=("neut","Spot N/A",0)

    # L3 VIX Monitor
    if vix:
        if vix<12:   ag["l3"]=("bull",f"VIX {vix:.1f} VERY CALM",85)
        elif vix<15: ag["l3"]=("bull",f"VIX {vix:.1f} CALM",70)
        elif vix<18: ag["l3"]=("neut",f"VIX {vix:.1f} CAUTION",50)
        elif vix<22: ag["l3"]=("bear",f"VIX {vix:.1f} HIGH FEAR",70)
        else:        ag["l3"]=("bear",f"VIX {vix:.1f} EXTREME DANGER",90)
    else: ag["l3"]=("neut","VIX N/A",0)

    # L4 GIFT Tracker
    if gd is not None:
        if gd>150:    ag["l4"]=("bull",f"GIFT +{round(gd)} STRONG GAP UP",80)
        elif gd>60:   ag["l4"]=("bull",f"GIFT +{round(gd)} mild up",60)
        elif gd<-150: ag["l4"]=("bear",f"GIFT {round(gd)} STRONG GAP DOWN",80)
        elif gd<-60:  ag["l4"]=("bear",f"GIFT {round(gd)} mild down",60)
        else:         ag["l4"]=("neut",f"GIFT flat ±{round(abs(gd))}",50)
    else: ag["l4"]=("neut","GIFT N/A",0)

    # L5 CE Premium
    if ce:
        chg=(ce-ce_p) if ce_p else 0
        if chg>5:    ag["l5"]=("bull",f"CE ₹{ce:.0f} +{chg:.0f} rising",70)
        elif chg<-5: ag["l5"]=("bear",f"CE ₹{ce:.0f} {chg:.0f} falling",65)
        else:        ag["l5"]=("neut",f"CE ₹{ce:.0f} stable",50)
    else: ag["l5"]=("neut","CE N/A",0)

    # L6 PE Premium
    if pe:
        chg=(pe-pe_p) if pe_p else 0
        if chg>5:    ag["l6"]=("bear",f"PE ₹{pe:.0f} +{chg:.0f} rising",70)
        elif chg<-5: ag["l6"]=("bull",f"PE ₹{pe:.0f} {chg:.0f} falling",65)
        else:        ag["l6"]=("neut",f"PE ₹{pe:.0f} stable",50)
    else: ag["l6"]=("neut","PE N/A",0)

    # L7 Session Clock
    if mins<555:    ag["l7"]=("neut","Pre-market",30)
    elif mins<600:  ag["l7"]=("bull","OPEN HOUR 9:15",80)
    elif mins<660:  ag["l7"]=("bull","PRIME 9:15-11:00",75)
    elif mins<780:  ag["l7"]=("neut","Mid 11-1pm",50)
    elif mins<870:  ag["l7"]=("neut","Afternoon 1-2:30",50)
    elif mins<930:  ag["l7"]=("neut","EXPIRY WINDOW 2:30-3:30",60)
    else:           ag["l7"]=("neut","Post market",20)

    # L8 Expiry Watcher
    if exp is not None:
        if exp==0:   ag["l8"]=("bull","TODAY EXPIRY ⚡",85)
        elif exp==1: ag["l8"]=("neut","TOMORROW EXPIRY",65)
        elif exp<=3: ag["l8"]=("neut",f"{exp} days near expiry",55)
        else:        ag["l8"]=("neut",f"{exp} days to expiry",50)
    else: ag["l8"]=("neut","Expiry N/A",0)

    # L9 Gap Detector
    if gap:
        if gap>100:    ag["l9"]=("bull",f"GAP UP +{round(gap)} STRONG",80)
        elif gap>40:   ag["l9"]=("bull",f"GAP UP +{round(gap)} mild",60)
        elif gap<-100: ag["l9"]=("bear",f"GAP DOWN {round(gap)} STRONG",80)
        elif gap<-40:  ag["l9"]=("bear",f"GAP DOWN {round(gap)} mild",60)
        else:          ag["l9"]=("neut",f"Flat ±{round(abs(gap))}",50)
    else: ag["l9"]=("neut","Gap N/A",0)

    # L10 PCR Engine
    if pcr:
        if pcr>1.5:   ag["l10"]=("bull",f"PCR {pcr} Strong bull confirm",85)
        elif pcr>1.2: ag["l10"]=("bull",f"PCR {pcr} Bull momentum",70)
        elif pcr<0.6: ag["l10"]=("bear",f"PCR {pcr} Strong bear",85)
        elif pcr<0.8: ag["l10"]=("bear",f"PCR {pcr} Bear bias",70)
        else:         ag["l10"]=("neut",f"PCR {pcr} Neutral",50)
    else: ag["l10"]=("neut","PCR N/A",0)

    # L11 Trap Detector
    trap=False; trap_det=""
    if pcr and spot and atm:
        if pcr>1.3 and spot<atm-50:
            trap=True; trap_det="PCR Bull + Price below ATM = BULL TRAP!"
        elif pcr<0.75 and spot>atm+50:
            trap=True; trap_det="PCR Bear + Price above ATM = BEAR TRAP!"
    if vix and vix>20 and pcr and pcr>1.2:
        trap=True; trap_det=f"VIX {vix:.1f} + PCR {pcr} = Manipulation!"
    ag["l11"]=("neut",f"⚠️ {trap_det}",80) if trap else ("bull","No trap detected",70)

    # L12 Risk Control
    if vix and vix>22:        ag["l12"]=("bear",f"VIX {vix:.1f} EXTREME — No trade!",95)
    elif vix and vix>18:      ag["l12"]=("neut",f"VIX {vix:.1f} — 1 lot max tight SL",70)
    elif exp==0 and mins>=870:ag["l12"]=("neut","Last hour expiry — careful",65)
    else:                     ag["l12"]=("bull","Risk OK — Normal position",70)

    # L13 Behaviour AI Master
    b=sum(1 for v in ag.values() if v[0]=="bull")
    r=sum(1 for v in ag.values() if v[0]=="bear")
    total=b+r; ratio=(b-r)/total if total>0 else 0
    avg_conf=sum(v[2] for v in ag.values())/len(ag)
    if ratio>0.3 and (not vix or vix<18) and not trap:
        ag["l13"]=("bull",f"BEHAVIOUR: BULL context ({b}↑{r}↓) conf:{avg_conf:.0f}%",int(avg_conf))
    elif ratio<-0.3 and not trap:
        ag["l13"]=("bear",f"BEHAVIOUR: BEAR context ({b}↑{r}↓) conf:{avg_conf:.0f}%",int(avg_conf))
    else:
        ag["l13"]=("neut",f"BEHAVIOUR: MIXED ({b}↑{r}↓) conf:{avg_conf:.0f}%",int(avg_conf))

    return ag, trap

# ── L14 NAMBI ─────────────────────────────────────────────────────────
def run_nambi(ag, trap):
    bw=brw=0.0; reasons=[]
    for aid,(sig,det,conf) in ag.items():
        w=WEIGHTS.get(aid,1.0)*(conf/100)
        if sig=="bull":   bw+=w;  reasons.append(det)
        elif sig=="bear": brw+=w; reasons.append(det)
    tw=bw+brw or 1
    bp=round(bw/tw*100); brp=100-bp
    diff=abs(bw-brw)
    conf="HIGH" if diff>=3 else "MEDIUM" if diff>=1.5 else "LOW"
    b_agents=sum(1 for v in ag.values() if v[0]=="bull")
    r_agents=sum(1 for v in ag.values() if v[0]=="bear")
    if trap:              sig="WAIT"; nv=f"NAMBI: WAIT — Trap! ({b_agents}↑{r_agents}↓)"
    elif bp>=65:          sig="BUY CE"; nv=f"NAMBI: BUY CE ✅ ({b_agents}↑{r_agents}↓)"
    elif brp>=65:         sig="BUY PE"; nv=f"NAMBI: BUY PE ✅ ({b_agents}↑{r_agents}↓)"
    else:                 sig="WAIT"; nv=f"NAMBI: WAIT — No clear signal ({b_agents}↑{r_agents}↓)"
    return sig,bp,brp,conf,reasons[:6],nv

# ── L15 TRUTH ENGINE ──────────────────────────────────────────────────
def run_truth_engine(snap):
    spot=snap.get("nifty"); pcr=snap.get("pcr")
    ce=snap.get("ce_prem"); pe=snap.get("pe_prem")
    sup=snap.get("support"); res=snap.get("resistance")
    if not all([spot,pcr,ce,pe]): return "UNKNOWN","Insufficient data"
    # Price confirms OI?
    price_bull = spot > (sup or 0)
    pcr_bull   = pcr > 1.0
    prem_bull  = (ce or 0) > (pe or 0)
    bull_count = sum([price_bull, pcr_bull, prem_bull])
    if bull_count>=3:   return "TRUE BULL MOVE","Price+OI+Premium all confirm BULL"
    elif bull_count==0: return "TRUE BEAR MOVE","Price+OI+Premium all confirm BEAR"
    elif bull_count==1: return "FAKE MOVE","Only 1/3 confirm — likely trap"
    else:               return "UNCLEAR","2/3 confirm — wait for clarity"

# ── L16 CONTRADICTION ENGINE ──────────────────────────────────────────
def run_contradiction_engine(snap):
    pcr=snap.get("pcr"); call_oi=snap.get("call_oi"); put_oi=snap.get("put_oi")
    ce=snap.get("ce_prem"); pe=snap.get("pe_prem")
    ce_p=snap.get("ce_prev"); pe_p=snap.get("pe_prev")
    if not all([pcr,call_oi,put_oi]): return "NONE","No data"
    # Smart money trap detection
    ce_rising = ce and ce_p and ce>ce_p+3
    pe_rising  = pe and pe_p and pe>pe_p+3
    if pcr>1.2 and ce_rising:
        return "BULL TRAP","PCR Bullish + CE rising = Smart money selling calls! BUY PE"
    elif pcr<0.8 and pe_rising:
        return "BEAR TRAP","PCR Bearish + PE rising = Smart money selling puts! BUY CE"
    elif pcr>1.2 and pe_rising:
        return "TRUE BULL","PCR + PE rising = Confirmed BULL move"
    elif pcr<0.8 and ce_rising:
        return "TRUE BEAR","PCR + CE rising = Confirmed BEAR move"
    else:
        return "NEUTRAL","No contradiction detected"

# ── L17 SELF-LEARNING ─────────────────────────────────────────────────
def update_learning(signal, pnl):
    """Update agent weights based on trade outcome."""
    global WEIGHTS
    with LOCK:
        agents_snap={k:v["signal"] for k,v in AGENTS.items()}
    correct_signal = "bull" if pnl>0 and signal=="BUY CE" else \
                     "bear" if pnl>0 and signal=="BUY PE" else None
    wrong_signal   = "bull" if pnl<0 and signal=="BUY CE" else \
                     "bear" if pnl<0 and signal=="BUY PE" else None
    note=""
    for aid,sig in agents_snap.items():
        if sig==correct_signal:
            WEIGHTS[aid]=min(WEIGHTS.get(aid,1.0)*1.05, 4.0)
            note+=f"{aid}↑ "
        elif sig==wrong_signal:
            WEIGHTS[aid]=max(WEIGHTS.get(aid,1.0)*0.95, 0.3)
            note+=f"{aid}↓ "
    log.info(f"L17 Learning: pnl={pnl} weights_updated: {note}")
    return note

# ── TELEGRAM ALERT ────────────────────────────────────────────────────
def send_telegram(msg):
    if not TELEGRAM["token"] or not TELEGRAM["chat_id"]: return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM['token']}/sendMessage",
            json={"chat_id":TELEGRAM["chat_id"],"text":msg,"parse_mode":"HTML"},
            timeout=5)
    except: pass

# ── FULL CYCLE ────────────────────────────────────────────────────────
def full_cycle():
    status,is_open=market_status()
    with LOCK:
        M["market_status"]=status
        SYS["market_status"]=status

    # Layer 1: Data
    fetch_yahoo_all()
    if is_open:
        ok=fetch_nse_oi(SYS["index"])
        if not ok:
            estimate_oi()
            with LOCK: SYS["error"]="NSE OI unavailable"
    else:
        estimate_oi()

    with LOCK:
        snap=dict(M); sys_snap=dict(SYS)

    # Layer 2: L1-L13 Agents
    ag,trap=run_agents_l1_l13(snap,sys_snap)

    # Layer 5: L15 Truth Engine
    truth,truth_reason=run_truth_engine(snap)

    # Layer 6: L16 Contradiction Engine
    contradiction,contra_reason=run_contradiction_engine(snap)

    # Adjust trap based on L16
    if "TRAP" in contradiction: trap=True

    # Layer 4: L14 NAMBI
    sig,bp,brp,conf,reasons,nv=run_nambi(ag,trap)

    # Final contradiction override
    if contradiction=="BULL TRAP" and sig=="BUY CE":
        sig="BUY PE"; nv="L16 OVERRIDE: Bull trap detected → BUY PE!"
    elif contradiction=="BEAR TRAP" and sig=="BUY PE":
        sig="BUY CE"; nv="L16 OVERRIDE: Bear trap detected → BUY CE!"

    # L14 final for agents
    b_all=sum(1 for v in ag.values() if v[0]=="bull")
    r_all=sum(1 for v in ag.values() if v[0]=="bear")
    n_all=sum(1 for v in ag.values() if v[0]=="neut")
    if trap:              ag["l14"]=("neut",f"NAMBI WAIT — Trap! ({b_all}↑{r_all}↓{n_all}◆)",80)
    elif sig=="BUY CE":   ag["l14"]=("bull",nv,80)
    elif sig=="BUY PE":   ag["l14"]=("bear",nv,80)
    else:                 ag["l14"]=("neut",nv,60)

    # Update state
    with LOCK:
        for aid,(s,d,c) in ag.items():
            AGENTS[aid]={"signal":s,"detail":d,"confidence":c,"weight":WEIGHTS.get(aid,1.0)}
        BRAIN.update({
            "signal":sig,"bull_pct":bp,"bear_pct":brp,
            "confidence":conf,"reasons":reasons,
            "trap":trap,"nambi_verdict":nv,"nambi_reason":ag["l14"][1],
            "truth":truth,"truth_reason":truth_reason,
            "contradiction":contradiction,"contra_reason":contra_reason,
        })
        if is_open: SYS["count"]+=1
        SYS["error"]=None

    log.info(f"HEMAN: {sig} | B:{bp}% Br:{brp}% | {conf} | Truth:{truth} | Contra:{contradiction}")

def poll_loop():
    while True:
        time.sleep(15)
        try: full_cycle()
        except Exception as e: log.error(f"Poll: {e}")

def keep_alive():
    time.sleep(60)
    while True:
        try:
            requests.get(f"http://localhost:{PORT}/ping",timeout=5)
            with LOCK: SYS["keep_alive_count"]+=1
        except: pass
        time.sleep(600)

# ── HTML DASHBOARD ────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<title>MATHAN AI HEMAN</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet"/>
<style>
:root{--bg:#070b0f;--bg2:#0d1419;--bg3:#111820;--brd:#1e2d3d;
  --gold:#f0a500;--grn:#00e676;--red:#ff1744;--blu:#29b6f6;
  --pur:#ce93d8;--orn:#ff9800;--txt:#cdd9e5;--dim:#4a6278;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--txt);font-family:'Rajdhani',sans-serif;padding-bottom:55px;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(240,165,0,.4)}70%{box-shadow:0 0 0 8px rgba(240,165,0,0)}}
.hdr{position:sticky;top:0;z-index:100;
  background:linear-gradient(180deg,#0a1118,rgba(7,11,15,.97));
  border-bottom:2px solid var(--gold);padding:10px 14px;
  display:flex;align-items:center;justify-content:space-between;}
.logo{font-family:'Orbitron';font-size:11px;font-weight:900;color:var(--gold);}
.logo small{display:block;font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-top:1px;}
.hclock{font-family:'Orbitron';font-size:12px;color:var(--gold);}
.hlive{font-size:9px;font-family:'Share Tech Mono';padding:2px 7px;border-radius:3px;}
.hlive.on{border:1px solid var(--grn);color:var(--grn);}
.hlive.off{border:1px solid var(--red);color:var(--red);}
.sbar{display:flex;justify-content:space-between;padding:4px 12px;
  background:var(--bg2);border-bottom:1px solid var(--brd);
  font-family:'Share Tech Mono';font-size:9px;}
.sdot{width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:middle;}
.sdot.ok{background:var(--grn);}.sdot.wait{background:var(--gold);animation:blink 1s infinite;}.sdot.err{background:var(--red);}
.main{padding:10px;max-width:480px;margin:0 auto;}
.mstatus{text-align:center;padding:6px;border-radius:8px;font-family:'Share Tech Mono';font-size:9px;margin-bottom:9px;border:1px solid;}
.mstatus.open{border-color:var(--grn);color:var(--grn);background:rgba(0,230,118,.06);}
.mstatus.closed{border-color:var(--gold);color:var(--gold);background:rgba(240,165,0,.06);}
.card{background:var(--bg2);border:1px solid var(--brd);border-radius:12px;padding:12px;margin-bottom:9px;}
.ctitle{font-family:'Orbitron';font-size:9px;color:var(--gold);letter-spacing:1px;margin-bottom:9px;display:flex;justify-content:space-between;align-items:center;}
.badge{display:inline-flex;padding:1px 7px;border-radius:8px;font-family:'Share Tech Mono';font-size:7px;}
.badge.live{background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.3);color:var(--grn);}
.badge.wait{background:rgba(41,182,246,.08);border:1px solid rgba(41,182,246,.2);color:var(--blu);}
.badge.warn{background:rgba(255,23,68,.08);border:1px solid rgba(255,23,68,.2);color:var(--red);}
.inp{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:6px;color:var(--txt);padding:8px 10px;font-size:12px;font-family:'Share Tech Mono';outline:none;margin-bottom:6px;}
.inp-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:3px;}
.cbtn{width:100%;padding:11px;border-radius:8px;cursor:pointer;font-family:'Orbitron';font-size:9px;font-weight:700;letter-spacing:1px;border:1px solid var(--orn);background:rgba(255,152,0,.08);color:var(--orn);margin-top:5px;}
.cbtn.ok{border-color:var(--pur);background:rgba(206,147,216,.1);color:var(--pur);}
.cbtn.yahoo{border-color:var(--gold);background:rgba(240,165,0,.08);color:var(--gold);}
.btn-row{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:6px;}
.ki{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:6px;color:var(--grn);padding:8px;font-size:12px;font-family:'Share Tech Mono';outline:none;}
.idx-row{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.ib{background:var(--bg3);border:2px solid var(--brd);border-radius:9px;padding:9px;text-align:center;cursor:pointer;}
.ib.on{border-color:var(--gold);}
.ib-name{font-family:'Orbitron';font-size:13px;font-weight:900;}
.ib.on .ib-name{color:var(--gold);}
.ib-spot{font-family:'Share Tech Mono';font-size:11px;color:var(--grn);margin-top:2px;}
.ib-atm{font-family:'Share Tech Mono';font-size:8px;color:var(--blu);margin-top:1px;}
.gift-box{background:var(--bg2);border:1px solid var(--brd);border-radius:11px;padding:10px 13px;margin-bottom:9px;display:flex;justify-content:space-between;align-items:center;position:relative;overflow:hidden;}
.gift-box::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--gold);}
.mstrip{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-bottom:9px;}
.mc{background:var(--bg2);border:1px solid var(--brd);border-radius:8px;padding:7px;text-align:center;}
.mc-n{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:2px;}
.mc-v{font-family:'Orbitron';font-size:13px;font-weight:700;}
.oi-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.oi-cell{background:var(--bg3);border-radius:7px;padding:8px;text-align:center;border:1px solid var(--brd);}
.oi-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:2px;}
.oi-val{font-family:'Orbitron';font-size:14px;font-weight:700;}
.pcr-bg{height:10px;border-radius:5px;background:rgba(255,255,255,.05);overflow:hidden;margin-bottom:4px;}
.pcr-fill{height:100%;border-radius:5px;transition:width .8s;}
.sr-row{display:grid;grid-template-columns:1fr 1fr;gap:6px;}
.sr-cell{border-radius:7px;padding:8px;text-align:center;}
.sr-sup{background:rgba(0,230,118,.07);border:1px solid rgba(0,230,118,.2);}
.sr-res{background:rgba(255,23,68,.07);border:1px solid rgba(255,23,68,.2);}
.prem-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;}
.prem-cell{background:var(--bg3);border-radius:8px;padding:9px;border:2px solid var(--brd);text-align:center;}
/* AGENTS */
.ag-sect{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:2px;margin:8px 0 5px;}
.ag-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:4px;}
.agc{background:var(--bg3);border:1px solid var(--brd);border-radius:8px;padding:7px;position:relative;overflow:hidden;}
.agc::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--brd);}
.agc.bull::before{background:var(--grn);}.agc.bear::before{background:var(--red);}.agc.neut::before{background:var(--gold);}
.ag-top{display:flex;justify-content:space-between;margin-bottom:1px;}
.ag-id{font-family:'Orbitron';font-size:7px;color:var(--dim);}
.ag-sig{font-family:'Share Tech Mono';font-size:8px;font-weight:700;}
.ag-sig.bull{color:var(--grn);}.ag-sig.bear{color:var(--red);}.ag-sig.neut{color:var(--gold);}.ag-sig.none{color:var(--dim);}
.ag-name{font-size:9px;font-weight:700;margin-bottom:1px;}
.ag-val{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);line-height:1.3;}
.ag-conf{font-family:'Share Tech Mono';font-size:7px;color:var(--blu);margin-top:1px;}
/* L15 L16 */
.engine-card{border-radius:10px;padding:9px;margin-bottom:7px;border:1px solid;}
.engine-card.truth{border-color:rgba(41,182,246,.3);background:rgba(41,182,246,.04);}
.engine-card.contra{border-color:rgba(206,147,216,.3);background:rgba(206,147,216,.04);}
.engine-title{font-family:'Orbitron';font-size:8px;letter-spacing:1px;margin-bottom:4px;}
.engine-val{font-family:'Share Tech Mono';font-size:10px;font-weight:700;}
.engine-reason{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-top:3px;}
/* NAMBI */
.nambi-card{background:linear-gradient(135deg,rgba(240,165,0,.08),rgba(240,165,0,.02));
  border:2px solid rgba(240,165,0,.5);border-radius:12px;padding:12px;margin-top:8px;
  animation:pulse 3s infinite;}
.nambi-verdict{font-family:'Orbitron';font-size:18px;font-weight:900;margin-bottom:4px;}
/* CONF */
.conf-track{height:10px;border-radius:5px;background:rgba(255,255,255,.05);overflow:hidden;display:flex;margin-bottom:3px;}
.conf-bull{height:100%;background:linear-gradient(90deg,#004d40,var(--grn));transition:width .7s;}
.conf-bear{height:100%;background:linear-gradient(90deg,var(--red),#7f0000);transition:width .7s;}
/* BRAIN */
.brain-box{border-radius:13px;padding:14px;margin-bottom:9px;border:2px solid var(--brd);}
.brain-box.bull{border-color:rgba(0,230,118,.6);background:linear-gradient(135deg,rgba(0,230,118,.07),transparent);}
.brain-box.bear{border-color:rgba(255,23,68,.6);background:linear-gradient(135deg,rgba(255,23,68,.07),transparent);}
.brain-box.wait{border-color:rgba(240,165,0,.5);background:linear-gradient(135deg,rgba(240,165,0,.05),transparent);}
.brain-sig{font-family:'Orbitron';font-size:24px;font-weight:900;margin-bottom:4px;}
/* L17 */
.learning-box{background:var(--bg2);border:1px solid rgba(41,182,246,.2);border-radius:9px;padding:9px;margin-bottom:9px;}
.go-btn{width:100%;padding:15px;border-radius:13px;border:none;cursor:pointer;
  background:linear-gradient(135deg,#7a5200,var(--gold));
  color:#000;font-family:'Orbitron';font-size:12px;font-weight:900;letter-spacing:2px;margin-bottom:9px;}
.go-btn:disabled{background:#1a2230;color:var(--dim);}
.ref-btn{width:100%;padding:9px;border-radius:9px;cursor:pointer;
  border:1px solid rgba(41,182,246,.4);background:rgba(41,182,246,.05);
  color:var(--blu);font-family:'Orbitron';font-size:9px;letter-spacing:1px;margin-bottom:9px;}
.claude-box{background:var(--bg2);border:1px solid rgba(240,165,0,.2);border-radius:11px;padding:12px;margin-bottom:9px;}
.wsbar{position:fixed;bottom:0;left:0;right:0;z-index:200;padding:4px 12px;
  font-family:'Share Tech Mono';font-size:9px;background:var(--bg2);
  border-top:1px solid var(--brd);display:flex;align-items:center;gap:6px;}
.wsdot{width:6px;height:6px;border-radius:50%;background:var(--red);flex-shrink:0;}
.wsdot.on{background:var(--grn);}
.sp{display:inline-block;width:11px;height:11px;border:2px solid rgba(0,0,0,.3);
  border-top-color:#000;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;margin-right:4px;}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo">MATHAN AI HEMAN<small>HIGH EFFICIENCY MARKET ADAPTIVE NETWORK</small></div>
  <div style="display:flex;align-items:center;gap:8px;">
    <div class="hclock" id="clock">--:--:--</div>
    <div class="hlive off" id="live-badge">OFFLINE</div>
  </div>
</div>
<div class="sbar">
  <div><span class="sdot wait" id="sdot"></span><span id="stxt" style="color:var(--gold)">Starting HEMAN...</span></div>
  <span id="rtxt" style="color:var(--dim)">IST</span>
</div>

<div class="main">

<div class="mstatus closed" id="mstatus-box"><span id="mstatus-txt">Checking...</span></div>

<!-- ANGEL ONE -->
<div class="card" style="border-color:rgba(206,147,216,.3);">
  <div class="ctitle" style="color:var(--pur);">ANGEL ONE — LIVE DATA
    <span id="angel-st" style="font-family:'Share Tech Mono';font-size:8px;color:var(--dim)">NOT SET</span>
  </div>
  <div class="inp-lbl">API KEY</div><input class="inp" id="api-key" type="password" placeholder="jYAKgdt3"/>
  <div class="inp-lbl">CLIENT ID</div><input class="inp" id="client-id" type="text" placeholder="V542909"/>
  <div class="inp-lbl">PIN</div><input class="inp" id="angel-pin" type="password" placeholder="1818"/>
  <div class="inp-lbl">TOTP SECRET</div><input class="inp" id="totp-secret" type="password" placeholder="KJ4MRMUWNTFTCUALRBH5ALKA7A"/>
  <div class="btn-row">
    <button class="cbtn" id="angel-btn" onclick="connectAngel()">CONNECT ANGEL ONE</button>
    <button class="cbtn yahoo" onclick="setYahoo()">YAHOO FALLBACK</button>
  </div>
</div>

<!-- CLAUDE KEY -->
<div class="card" style="border-color:rgba(41,182,246,.2);">
  <div class="ctitle" style="color:var(--blu);">CLAUDE AI KEY</div>
  <input class="ki" id="ki" type="password" placeholder="sk-ant-..." oninput="saveKey()"/>
</div>

<!-- INDEX -->
<div class="idx-row">
  <div class="ib on" id="ib-nifty" onclick="setIdx('NIFTY')">
    <div class="ib-name">NIFTY 50</div>
    <div class="ib-spot" id="n-spot">—</div><div class="ib-atm" id="n-atm">ATM: —</div>
  </div>
  <div class="ib" id="ib-sensex" onclick="setIdx('SENSEX')">
    <div class="ib-name">SENSEX</div>
    <div class="ib-spot" id="s-spot">—</div><div class="ib-atm" id="s-atm">ATM: —</div>
  </div>
</div>

<!-- GIFT -->
<div class="gift-box">
  <div>
    <div style="font-family:'Share Tech Mono';font-size:7px;color:var(--gold);margin-bottom:2px">GIFT NIFTY — TOMORROW SENTIMENT</div>
    <div style="font-family:'Orbitron';font-size:20px;font-weight:900" id="gv">—</div>
    <div style="font-family:'Share Tech Mono';font-size:9px;margin-top:2px" id="gc">—</div>
  </div>
  <div style="background:var(--bg3);border-radius:7px;padding:6px 9px;text-align:center;min-width:90px;">
    <div style="font-family:'Share Tech Mono';font-size:7px;color:var(--dim)">MOOD</div>
    <div style="font-size:12px;font-weight:700;margin-top:2px" id="gs">—</div>
  </div>
</div>

<!-- MARKET STRIP -->
<div class="mstrip">
  <div class="mc"><div class="mc-n">NIFTY</div><div class="mc-v" id="nv" style="color:var(--grn)">—</div><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--blu)" id="na">ATM: —</div></div>
  <div class="mc"><div class="mc-n">SENSEX</div><div class="mc-v" id="sv" style="color:var(--grn)">—</div><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--blu)" id="sa">—</div></div>
  <div class="mc"><div class="mc-n">VIX</div><div class="mc-v" id="vv" style="color:var(--gold)">—</div><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--dim)" id="vn">—</div></div>
</div>

<!-- OI -->
<div class="card">
  <div class="ctitle">OI ANALYSIS <span class="badge wait" id="oi-src">LOADING</span></div>
  <div class="oi-grid">
    <div class="oi-cell"><div class="oi-lbl">CALL OI</div><div class="oi-val" id="callOI" style="color:var(--red)">—</div></div>
    <div class="oi-cell"><div class="oi-lbl">PUT OI</div><div class="oi-val" id="putOI" style="color:var(--grn)">—</div></div>
  </div>
  <div style="background:var(--bg3);border-radius:7px;padding:8px 9px;margin-bottom:7px;">
    <div style="display:flex;justify-content:space-between;font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-bottom:5px;">
      <span>PCR</span><span id="pcrVal" style="color:var(--gold)">—</span>
    </div>
    <div class="pcr-bg"><div class="pcr-fill" id="pcrFill" style="width:50%;background:var(--gold)"></div></div>
    <div style="display:flex;justify-content:space-between;font-family:'Share Tech Mono';font-size:7px;color:var(--dim)"><span>BEAR &lt;0.7</span><span>NEUTRAL 1.0</span><span>BULL &gt;1.2</span></div>
    <div style="font-family:'Share Tech Mono';font-size:10px;margin-top:5px;text-align:center" id="pcrSig">—</div>
  </div>
  <div class="sr-row">
    <div class="sr-cell sr-sup"><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--grn)">SUPPORT</div><div style="font-family:'Orbitron';font-size:14px;color:var(--grn)" id="support">—</div></div>
    <div class="sr-cell sr-res"><div style="font-family:'Share Tech Mono';font-size:7px;color:var(--red)">RESISTANCE</div><div style="font-family:'Orbitron';font-size:14px;color:var(--red)" id="resistance">—</div></div>
  </div>
</div>

<!-- PREMIUM -->
<div class="card">
  <div class="ctitle">ATM PREMIUM <span class="badge wait" id="prem-src">LOADING</span></div>
  <div class="prem-grid">
    <div class="prem-cell"><div style="font-family:'Orbitron';font-size:10px;color:var(--grn);margin-bottom:3px">CALL CE</div><div style="font-family:'Orbitron';font-size:22px;font-weight:700;color:var(--grn)" id="cePrem">—</div></div>
    <div class="prem-cell"><div style="font-family:'Orbitron';font-size:10px;color:var(--red);margin-bottom:3px">PUT PE</div><div style="font-family:'Orbitron';font-size:22px;font-weight:700;color:var(--red)" id="pePrem">—</div></div>
  </div>
</div>

<!-- L15 TRUTH ENGINE -->
<div class="engine-card truth">
  <div class="engine-title" style="color:var(--blu)">⚡ L15 — MARKET TRUTH ENGINE</div>
  <div class="engine-val" id="truth-val" style="color:var(--blu)">UNKNOWN</div>
  <div class="engine-reason" id="truth-reason">Awaiting data...</div>
</div>

<!-- L16 CONTRADICTION ENGINE -->
<div class="engine-card contra">
  <div class="engine-title" style="color:var(--pur)">🔍 L16 — OI/PCR CONTRADICTION ENGINE</div>
  <div class="engine-val" id="contra-val" style="color:var(--pur)">NONE</div>
  <div class="engine-reason" id="contra-reason">Awaiting data...</div>
</div>

<!-- AGENTS L1-L13 + NAMBI L14 -->
<div class="card">
  <div class="ctitle">CCS AGENTS — L1 TO L13 <span class="badge wait" id="ag-badge">WAITING</span></div>
  <div class="ag-sect">▸ MARKET DATA (L1-L4)</div>
  <div class="ag-grid">
    <div class="agc" id="card-l1"><div class="ag-top"><span class="ag-id">L1</span><span class="ag-sig none" id="sig-l1">—</span></div><div class="ag-name">OI Analyst</div><div class="ag-val" id="val-l1">—</div><div class="ag-conf" id="conf-l1"></div></div>
    <div class="agc" id="card-l2"><div class="ag-top"><span class="ag-id">L2</span><span class="ag-sig none" id="sig-l2">—</span></div><div class="ag-name">Price Action</div><div class="ag-val" id="val-l2">—</div><div class="ag-conf" id="conf-l2"></div></div>
    <div class="agc" id="card-l3"><div class="ag-top"><span class="ag-id">L3</span><span class="ag-sig none" id="sig-l3">—</span></div><div class="ag-name">VIX Monitor</div><div class="ag-val" id="val-l3">—</div><div class="ag-conf" id="conf-l3"></div></div>
    <div class="agc" id="card-l4"><div class="ag-top"><span class="ag-id">L4</span><span class="ag-sig none" id="sig-l4">—</span></div><div class="ag-name">GIFT Tracker</div><div class="ag-val" id="val-l4">—</div><div class="ag-conf" id="conf-l4"></div></div>
  </div>
  <div class="ag-sect">▸ PREMIUM & SESSION (L5-L8)</div>
  <div class="ag-grid">
    <div class="agc" id="card-l5"><div class="ag-top"><span class="ag-id">L5</span><span class="ag-sig none" id="sig-l5">—</span></div><div class="ag-name">CE Premium</div><div class="ag-val" id="val-l5">—</div><div class="ag-conf" id="conf-l5"></div></div>
    <div class="agc" id="card-l6"><div class="ag-top"><span class="ag-id">L6</span><span class="ag-sig none" id="sig-l6">—</span></div><div class="ag-name">PE Premium</div><div class="ag-val" id="val-l6">—</div><div class="ag-conf" id="conf-l6"></div></div>
    <div class="agc" id="card-l7"><div class="ag-top"><span class="ag-id">L7</span><span class="ag-sig none" id="sig-l7">—</span></div><div class="ag-name">Session Clock</div><div class="ag-val" id="val-l7">—</div><div class="ag-conf" id="conf-l7"></div></div>
    <div class="agc" id="card-l8"><div class="ag-top"><span class="ag-id">L8</span><span class="ag-sig none" id="sig-l8">—</span></div><div class="ag-name">Expiry Watcher</div><div class="ag-val" id="val-l8">—</div><div class="ag-conf" id="conf-l8"></div></div>
  </div>
  <div class="ag-sect">▸ INTELLIGENCE (L9-L13)</div>
  <div class="ag-grid">
    <div class="agc" id="card-l9"><div class="ag-top"><span class="ag-id">L9</span><span class="ag-sig none" id="sig-l9">—</span></div><div class="ag-name">Gap Detector</div><div class="ag-val" id="val-l9">—</div><div class="ag-conf" id="conf-l9"></div></div>
    <div class="agc" id="card-l10"><div class="ag-top"><span class="ag-id">L10</span><span class="ag-sig none" id="sig-l10">—</span></div><div class="ag-name">PCR Engine</div><div class="ag-val" id="val-l10">—</div><div class="ag-conf" id="conf-l10"></div></div>
    <div class="agc" id="card-l11"><div class="ag-top"><span class="ag-id">L11</span><span class="ag-sig none" id="sig-l11">—</span></div><div class="ag-name">Trap Detector</div><div class="ag-val" id="val-l11">—</div><div class="ag-conf" id="conf-l11"></div></div>
    <div class="agc" id="card-l12"><div class="ag-top"><span class="ag-id">L12</span><span class="ag-sig none" id="sig-l12">—</span></div><div class="ag-name">Risk Control</div><div class="ag-val" id="val-l12">—</div><div class="ag-conf" id="conf-l12"></div></div>
  </div>
  <div style="margin-top:5px">
    <div class="agc" id="card-l13" style="border-color:rgba(41,182,246,.3)">
      <div class="ag-top"><span class="ag-id" style="color:var(--blu)">L13</span><span class="ag-sig none" id="sig-l13">—</span></div>
      <div class="ag-name" style="color:var(--blu)">Behaviour AI</div>
      <div class="ag-val" id="val-l13">—</div><div class="ag-conf" id="conf-l13"></div>
    </div>
  </div>
  <!-- Confidence -->
  <div style="background:var(--bg3);border-radius:8px;padding:9px;margin-top:8px">
    <div style="display:flex;justify-content:space-between;font-family:'Share Tech Mono';font-size:8px;margin-bottom:5px;">
      <span style="color:var(--grn)">BULL <span id="bp">50%</span></span>
      <span style="color:var(--gold)" id="conf-mid">Confidence: —</span>
      <span style="color:var(--red)">BEAR <span id="brp">50%</span></span>
    </div>
    <div class="conf-track">
      <div class="conf-bull" id="conf-bull" style="width:50%"></div>
      <div class="conf-bear" id="conf-bear" style="width:50%"></div>
    </div>
  </div>
  <!-- L14 NAMBI -->
  <div class="nambi-card">
    <div style="font-family:'Orbitron';font-size:9px;color:var(--gold);margin-bottom:4px;letter-spacing:2px">⚡ L14 — NAMBI (MASTER CONTROLLER)</div>
    <div class="nambi-verdict" id="nambi-verdict" style="color:var(--gold)">STANDBY</div>
    <div style="font-family:'Share Tech Mono';font-size:9px;color:var(--dim);margin-top:3px" id="nambi-reason">Waiting for all agents...</div>
    <div style="margin-top:6px;font-family:'Share Tech Mono';font-size:7px;color:var(--dim)">
      Chairman → NAMBI → L15 Truth → L16 Contradiction → L17 Learning → Signal
    </div>
  </div>
</div>

<!-- L17 SELF-LEARNING -->
<div class="learning-box">
  <div style="font-family:'Orbitron';font-size:8px;color:var(--blu);margin-bottom:5px;letter-spacing:1px">🧠 L17 — SELF-LEARNING ENGINE</div>
  <div style="font-family:'Share Tech Mono';font-size:9px;color:var(--dim)" id="learning-note">System tracking agent performance...</div>
  <div style="margin-top:6px;display:flex;gap:8px;flex-wrap:wrap" id="weight-display"></div>
</div>

<!-- BRAIN FINAL -->
<div class="brain-box wait" id="brain-box">
  <div style="font-family:'Share Tech Mono';font-size:8px;color:var(--dim);letter-spacing:2px;margin-bottom:4px">HEMAN BRAIN — FINAL DECISION</div>
  <div class="brain-sig" id="brain-sig" style="color:var(--gold)">LOADING...</div>
  <div style="font-size:11px;color:var(--dim);margin-bottom:8px" id="brain-sub">CCS + Truth + Contradiction → NAMBI</div>
  <div id="reasons" style="background:var(--bg3);border-radius:8px;padding:8px;font-family:'Share Tech Mono';font-size:9px;line-height:1.8"></div>
</div>

<button class="ref-btn" onclick="doFetch()">🔄 REFRESH NOW</button>
<button class="go-btn" id="go-btn" onclick="runClaude()">⚡ NAMBI + CLAUDE — CHAIRMAN REPORT</button>
<div class="claude-box" id="claude-box" style="display:none">
  <div style="font-family:'Orbitron';font-size:8px;color:var(--gold);margin-bottom:8px;letter-spacing:1px">CLAUDE AI — HEMAN CHAIRMAN REPORT</div>
  <div id="claude-text" style="font-size:13px;line-height:1.9"></div>
</div>

</div>

<div class="wsbar">
  <div class="wsdot" id="wsdot"></div>
  <span id="ws-txt">Starting HEMAN...</span>
  <span id="ws-cnt" style="margin-left:auto;color:var(--dim)"></span>
</div>

<script>
let D={},BR={},AG={},SY={};

async function poll(){
  try{
    const r=await fetch('/state',{signal:AbortSignal.timeout(10000)});
    if(!r.ok) throw new Error('HTTP '+r.status);
    const j=await r.json();
    D=j.market||{}; BR=j.brain||{}; AG=j.agents||{}; SY=j.sys||{};
    setOnline(); render();
  }catch(e){ setOffline('Reconnecting...'); }
}

function setOnline(){
  q('wsdot').className='wsdot on';
  q('live-badge').className='hlive on'; q('live-badge').textContent='LIVE';
  q('ws-txt').textContent='HEMAN Connected ✓';
}
function setOffline(msg){
  q('wsdot').className='wsdot';
  q('live-badge').className='hlive off'; q('live-badge').textContent='OFFLINE';
  q('ws-txt').textContent=msg;
}

function render(){
  const ms=D.market_status||SY.market_status||'';
  const isOpen=ms.includes('OPEN')&&!ms.includes('CLOSED')&&!ms.includes('PRE');
  q('mstatus-box').className='mstatus '+(isOpen?'open':'closed');
  t('mstatus-txt',ms||'Checking...');
  if(ms&&!isOpen) sdot('wait',ms); else sdot('ok','HEMAN Live #'+(SY.count||0)+' — '+(D.fetch_time||ist()));
  q('ws-cnt').textContent=D.source||'';

  const idx=SY.index||'NIFTY';
  q('ib-nifty').className='ib'+(idx==='NIFTY'?' on':'');
  q('ib-sensex').className='ib'+(idx==='SENSEX'?' on':'');

  if(D.nifty){ tv('nv',D.nifty.toFixed(0),'var(--grn)'); t('na','ATM: '+(D.atm||'—')); t('n-spot',D.nifty.toFixed(0)); t('n-atm','ATM: '+(D.atm||'—')); }
  if(D.sensex){ tv('sv',D.sensex.toFixed(0),'var(--grn)'); const sa='ATM: '+Math.round(D.sensex/100)*100; t('sa',sa); t('s-spot',D.sensex.toFixed(0)); t('s-atm',sa); }
  if(D.vix){ const vc=D.vix>20?'var(--red)':D.vix>15?'var(--gold)':'var(--grn)'; tv('vv',D.vix.toFixed(1),vc); t('vn',D.vix>20?'HIGH FEAR':D.vix>15?'CAUTION':'CALM'); }
  if(D.gift){ const gd=D.gift_diff||0; tv('gv',D.gift.toFixed(0),gd>=0?'var(--grn)':'var(--red)'); tv('gc',(gd>=0?'▲+':'▼')+Math.abs(gd).toFixed(0)+' pts',gd>=0?'var(--grn)':'var(--red)'); t('gs',gd>100?'BULLISH':gd>40?'MILD BULL':gd<-100?'BEARISH':gd<-40?'MILD BEAR':'NEUTRAL'); }

  if(D.call_oi){
    t('callOI',fmt(D.call_oi)); t('putOI',fmt(D.put_oi));
    const pcr=D.pcr||1;
    tv('pcrVal',pcr.toFixed(2),pcr>1.2?'var(--grn)':pcr<0.7?'var(--red)':'var(--gold)');
    q('pcrFill').style.width=Math.min(100,pcr/2*100)+'%';
    q('pcrFill').style.background=pcr>1.2?'var(--grn)':pcr<0.7?'var(--red)':'var(--gold)';
    tv('pcrSig',pcr>1.2?'📈 BULLISH':pcr<0.7?'📉 BEARISH':'⚖️ NEUTRAL',pcr>1.2?'var(--grn)':pcr<0.7?'var(--red)':'var(--gold)');
    q('oi-src').className='badge '+(D.source&&D.source.includes('NSE')?'live':'wait');
    q('oi-src').textContent=D.source&&D.source.includes('NSE')?'🟢 NSE REAL':D.source&&D.source.includes('EST')?'⚡ ESTIMATED':'LOADING';
  }
  if(D.support) tv('support',D.support.toLocaleString('en-IN'),'var(--grn)');
  if(D.resistance) tv('resistance',D.resistance.toLocaleString('en-IN'),'var(--red)');
  if(D.ce_prem){ tv('cePrem','₹'+D.ce_prem.toFixed(0),'var(--grn)'); q('prem-src').className='badge live'; q('prem-src').textContent='🟢 LIVE'; }
  if(D.pe_prem) tv('pePrem','₹'+D.pe_prem.toFixed(0),'var(--red)');

  // L15 Truth
  const tv15=BR.truth||'UNKNOWN';
  const tc15=tv15.includes('BULL')?'var(--grn)':tv15.includes('BEAR')?'var(--red)':tv15.includes('FAKE')?'var(--orn)':'var(--blu)';
  tv('truth-val',tv15,tc15); t('truth-reason',BR.truth_reason||'—');

  // L16 Contradiction
  const cv16=BR.contradiction||'NONE';
  const cc16=cv16.includes('TRAP')?'var(--red)':cv16.includes('TRUE')?'var(--grn)':'var(--pur)';
  tv('contra-val',cv16,cc16); t('contra-reason',BR.contra_reason||'—');

  // Agents L1-L13
  let live=0;
  for(let i=1;i<=13;i++){
    const aid='l'+i; const a=AG[aid]||{};
    const card=q('card-'+aid),sigEl=q('sig-'+aid),valEl=q('val-'+aid),confEl=q('conf-'+aid);
    if(!card) continue;
    const d=a.signal||'none';
    card.className='agc '+(d==='bull'||d==='bear'||d==='neut'?d:'');
    if(sigEl){ sigEl.className='ag-sig '+d; sigEl.textContent=d==='bull'?'▲ BULL':d==='bear'?'▼ BEAR':d==='neut'?'◆ HOLD':'—'; }
    if(valEl) valEl.textContent=a.detail||'—';
    if(confEl&&a.confidence) confEl.textContent=`Conf: ${a.confidence}% | Wt: ${(a.weight||1).toFixed(1)}`;
    if(d!=='none') live++;
  }
  q('ag-badge').className='badge '+(live>0?'live':'wait');
  q('ag-badge').textContent=live>0?`● ${live}/13 LIVE`:'WAITING';

  // Confidence bar
  const bp_=BR.bull_pct||50,brp_=BR.bear_pct||50;
  q('conf-bull').style.width=bp_+'%'; q('conf-bear').style.width=brp_+'%';
  t('bp',bp_+'%'); t('brp',brp_+'%');
  t('conf-mid','Confidence: '+(BR.confidence||'—'));

  // NAMBI L14
  const nv=BR.nambi_verdict||'STANDBY';
  const nc=nv.includes('BUY CE')?'var(--grn)':nv.includes('BUY PE')?'var(--red)':'var(--gold)';
  tv('nambi-verdict',nv,nc); t('nambi-reason',BR.nambi_reason||'—');

  // L17 weights display
  const wd=q('weight-display');
  if(wd&&AG){
    wd.innerHTML=Object.entries(AG).filter(([k])=>k!='l14').map(([k,a])=>
      `<span style="font-family:'Share Tech Mono';font-size:7px;color:var(--dim);
       background:var(--bg3);padding:2px 5px;border-radius:4px">
       ${k.toUpperCase()}: ${(a.weight||1).toFixed(2)}</span>`
    ).join('');
  }
  t('learning-note',BR.learning_note||'Tracking agent performance — weights auto-adjust on each trade');

  // Brain
  const sig=BR.signal||'WAIT';
  const cls=sig==='BUY CE'?'bull':sig==='BUY PE'?'bear':'wait';
  const col={bull:'var(--grn)',bear:'var(--red)',wait:'var(--gold)'}[cls];
  const lbl={bull:'🟢 BUY CE — BULLISH',bear:'🔴 BUY PE — BEARISH',wait:'⏳ WAIT — HOLD CAPITAL'}[cls];
  q('brain-box').className='brain-box '+cls;
  tv('brain-sig',lbl,col);
  t('brain-sub',(D.source||'—')+'  Bull:'+bp_+'%  Bear:'+brp_+'%  Conf:'+(BR.confidence||'—')+(BR.trap?' ⚠️TRAP':''));
  if(BR.reasons&&BR.reasons.length) q('reasons').innerHTML=BR.reasons.slice(0,5).map(r=>'▸ '+r).join('<br>');
}

async function connectAngel(){
  const ak=q('api-key').value.trim()||'jYAKgdt3';
  const ci=q('client-id').value.trim()||'V542909';
  const pin=q('angel-pin').value.trim()||'1818';
  const ts=q('totp-secret').value.trim()||'KJ4MRMUWNTFTCUALRBH5ALKA7A';
  q('angel-btn').textContent='Connecting...';
  try{
    const r=await fetch('/connect_angel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:ak,client_id:ci,pin:pin,totp_secret:ts})});
    const j=await r.json();
    if(j.ok){ q('angel-st').textContent='● LIVE'; q('angel-st').style.color='var(--pur)'; q('angel-btn').textContent='✅ CONNECTED'; q('angel-btn').className='cbtn ok'; }
    else{ q('angel-btn').textContent='CONNECT ANGEL ONE'; sdot('err','Angel: '+(j.error||'Failed')); }
  }catch(e){ q('angel-btn').textContent='CONNECT ANGEL ONE'; }
}
async function setYahoo(){ await fetch('/set_yahoo',{method:'POST'}).catch(()=>{}); setTimeout(poll,2000); }
function setIdx(idx){ q('ib-nifty').className='ib'+(idx==='NIFTY'?' on':''); q('ib-sensex').className='ib'+(idx==='SENSEX'?' on':''); fetch('/set_index',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:idx})}).then(()=>setTimeout(poll,2000)).catch(()=>{}); }
async function doFetch(){ sdot('wait','Fetching...'); await fetch('/do_fetch',{method:'POST'}).catch(()=>{}); setTimeout(poll,3000); }

async function runClaude(){
  const key=getKey();
  if(!key){ alert('Claude API Key enter பண்ணுங்க!'); return; }
  const btn=q('go-btn'); btn.disabled=true; btn.innerHTML='<span class="sp"></span>HEMAN Computing...';
  q('claude-box').style.display='block';
  q('claude-text').innerHTML='<span style="color:var(--gold)">HEMAN → L15 → L16 → NAMBI → Claude...</span>';
  q('claude-box').scrollIntoView({behavior:'smooth'});
  const agSum=Object.entries(AG).map(([id,a])=>`${id.toUpperCase()}: ${(a.signal||'N/A').toUpperCase()} — ${a.detail||''} (conf:${a.confidence||0}%)`).join('\n');
  const prompt=`MATHAN AI HEMAN — CHAIRMAN REPORT
Market Status: ${D.market_status||'Unknown'}
NIFTY: ${D.nifty?.toFixed(0)||'N/A'} | ATM: ${D.atm||'N/A'} | SENSEX: ${D.sensex?.toFixed(0)||'N/A'}
VIX: ${D.vix?.toFixed(1)||'N/A'} | PCR: ${D.pcr||'N/A'}
CE: ₹${D.ce_prem?.toFixed(0)||'N/A'} | PE: ₹${D.pe_prem?.toFixed(0)||'N/A'}
Support: ${D.support||'N/A'} | Resistance: ${D.resistance||'N/A'}

L15 TRUTH ENGINE: ${BR.truth||'UNKNOWN'} — ${BR.truth_reason||''}
L16 CONTRADICTION: ${BR.contradiction||'NONE'} — ${BR.contra_reason||''}
L14 NAMBI: ${BR.nambi_verdict||'STANDBY'}
Brain: ${BR.signal} | Bull:${BR.bull_pct}% Bear:${BR.bear_pct}% | ${BR.confidence}
Trap: ${BR.trap?'YES ⚠️':'NO'}

ALL AGENTS:
${agSum}

Give Chairman Mr. Mathan Sir (HEMAN system):
1. சாமி! NAMBI FINAL CALL
2. L15 Truth confirmation
3. L16 Trap check result
4. Strike + Entry condition
5. SL exact ₹ + T1/T2/T3
6. Risk warning
7. Tomorrow outlook

Tamil+English mixed. Bold key numbers.`;
  try{
    const r=await fetch('https://api.anthropic.com/v1/messages',{method:'POST',headers:{'Content-Type':'application/json','x-api-key':key,'anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'},body:JSON.stringify({model:'claude-sonnet-4-20250514',max_tokens:900,messages:[{role:'user',content:prompt}]}),signal:AbortSignal.timeout(35000)});
    const j=await r.json();
    q('claude-text').innerHTML=(j?.content?.[0]?.text||'Error').replace(/\n/g,'<br>').replace(/\*\*(.*?)\*\*/g,'<strong style="color:var(--gold)">$1</strong>');
  }catch(e){ q('claude-text').innerHTML='<span style="color:var(--red)">Error — Retry</span>'; }
  btn.disabled=false; btn.innerHTML='⚡ NAMBI + CLAUDE — CHAIRMAN REPORT';
}

function saveKey(){ const v=q('ki').value.trim(); if(v.startsWith('sk-ant')) try{localStorage.setItem('mbk',v);}catch(e){} }
function getKey(){ const v=q('ki').value.trim(); return v.startsWith('sk-ant')?v:(localStorage.getItem('mbk')||''); }
function fmt(n){ if(!n)return'—'; if(n>10000000)return(n/10000000).toFixed(1)+'Cr'; if(n>100000)return(n/100000).toFixed(1)+'L'; return(n/1000).toFixed(0)+'K'; }
function sdot(s,txt){ q('sdot').className='sdot '+s; q('stxt').textContent=txt; q('stxt').style.color=s==='ok'?'var(--grn)':s==='err'?'var(--red)':'var(--gold)'; }
function q(i){ return document.getElementById(i); }
function t(i,v){ const e=q(i); if(e) e.textContent=v; }
function tv(i,v,c){ const e=q(i); if(e){ e.textContent=v; if(c) e.style.color=c; } }
function ist(){ const n=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Kolkata'})); return [n.getHours(),n.getMinutes(),n.getSeconds()].map(x=>String(x).padStart(2,'0')).join(':'); }
setInterval(()=>{ const ts=ist(); t('clock',ts); t('rtxt','IST '+ts); },1000);
window.onload=()=>{
  const k=localStorage.getItem('mbk'); if(k) q('ki').value=k;
  q('api-key').value='jYAKgdt3'; q('client-id').value='V542909';
  q('angel-pin').value='1818'; q('totp-secret').value='KJ4MRMUWNTFTCUALRBH5ALKA7A';
  poll(); setInterval(poll,8000);
};
</script>
</body>
</html>"""

# ── REST ROUTES ───────────────────────────────────────────────────────
@app.route("/")
@app.route("/dashboard")
def dashboard():
    return Response(HTML, mimetype="text/html")

@app.route("/state")
def state_route():
    with LOCK:
        return jsonify({
            "market": dict(M),
            "brain":  dict(BRAIN),
            "agents": dict(AGENTS),
            "sys":    {**dict(SYS),"angel_ok":ANGEL["connected"]},
        })

@app.route("/ping")
def ping():
    return jsonify({"pong":True,"time":ist(),"system":"HEMAN","count":SYS["count"]})

@app.route("/connect_angel",methods=["POST"])
def connect_angel():
    d=request.get_json(force=True) or {}
    ak=d.get("api_key",ANGEL["api_key"]).strip()
    ci=d.get("client_id",ANGEL["client_id"]).strip()
    pin=d.get("pin",ANGEL["pin"]).strip()
    ts=d.get("totp_secret",ANGEL["totp_secret"]).strip()
    if not all([ak,ci,pin,ts]):
        return jsonify({"ok":False,"error":"All 4 fields required"}),400
    if not SMARTAPI_OK:
        return jsonify({"ok":False,"error":"SmartAPI not installed on server"}),500
    try:
        totp=pyotp.TOTP(ts).now()
        obj=SmartConnect(api_key=ak)
        data=obj.generateSession(ci,pin,totp)
        if not data or data.get("status") is False:
            msg=data.get("message","Login failed") if data else "No response"
            return jsonify({"ok":False,"error":msg}),401
        ANGEL.update({"api_key":ak,"client_id":ci,"pin":pin,"totp_secret":ts,
                      "jwt_token":data["data"]["jwtToken"],"connected":True})
        SYS["angel_ok"]=True
        threading.Thread(target=full_cycle,daemon=True).start()
        return jsonify({"ok":True,"msg":"Angel One connected!"})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)}),500

@app.route("/set_yahoo",methods=["POST"])
def set_yahoo():
    threading.Thread(target=full_cycle,daemon=True).start()
    return jsonify({"ok":True})

@app.route("/set_index",methods=["POST"])
def set_index():
    idx=(request.get_json(force=True) or {}).get("index","NIFTY").upper()
    if idx in INDEX_CFG:
        with LOCK: SYS["index"]=idx
        threading.Thread(target=full_cycle,daemon=True).start()
    return jsonify({"ok":True,"index":idx})

@app.route("/do_fetch",methods=["POST"])
def do_fetch():
    threading.Thread(target=full_cycle,daemon=True).start()
    return jsonify({"ok":True})

@app.route("/learning_update",methods=["POST"])
def learning_update():
    d=request.get_json(force=True) or {}
    sig=d.get("signal",""); pnl=float(d.get("pnl",0))
    note=update_learning(sig,pnl)
    with LOCK:
        BRAIN["learning_note"]=f"L17: {note[:80]}"
        SYS["trade_log"].append({"signal":sig,"pnl":pnl,"time":ist()})
        if pnl>0: SYS["win_count"]+=1
        elif pnl<0: SYS["loss_count"]+=1
        SYS["daily_pnl"]+=pnl
    return jsonify({"ok":True,"note":note,"weights":dict(WEIGHTS)})

# ── STARTUP ───────────────────────────────────────────────────────────
if __name__=="__main__":
    log.info("""
╔══════════════════════════════════════════════════╗
║   MATHAN AI HEMAN                               ║
║   High Efficiency Market Adaptive Network        ║
╠══════════════════════════════════════════════════╣
║   L1-L13 Agents + L14 NAMBI                     ║
║   L15 Truth + L16 Contradiction + L17 Learning  ║
║   From Behaviour to Decision to Intelligence    ║
╚══════════════════════════════════════════════════╝
    """)
    threading.Thread(target=full_cycle,daemon=True).start()
    threading.Thread(target=poll_loop,daemon=True).start()
    threading.Thread(target=keep_alive,daemon=True).start()
    app.run(host="0.0.0.0",port=PORT,use_reloader=False,threaded=True)
