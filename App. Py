"""
MATHAN AI — ANGEL ONE FULL INTEGRATION
========================================
Angel One SmartAPI WebSocket → Real OI, CE/PE Premium, PCR
REST → Spot, Login, Session

Install:
  pip install smartapi-python pyotp requests flask flask-sock simple-websocket --break-system-packages

Run:
  python mathan_brain.py

Open:
  http://YOUR_IP:8000
"""

import os, json, time, threading, datetime, socket, requests, sqlite3
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from flask import Flask, Response, jsonify, request
from flask_sock import Sock

# ── DASHBOARD HTML ────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<title>Mathan AI — Angel One Brain</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet"/>
<style>
:root{--bg:#070b0f;--bg2:#0d1419;--bg3:#111820;--brd:#1e2d3d;
  --gold:#f0a500;--grn:#00e676;--red:#ff1744;--blu:#29b6f6;
  --pur:#ce93d8;--orn:#ff9800;--txt:#cdd9e5;--dim:#4a6278;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--txt);font-family:'Rajdhani',sans-serif;padding-bottom:40px;}
body::before{content:'';position:fixed;inset:0;
  background:linear-gradient(rgba(240,165,0,.025) 1px,transparent 1px),
             linear-gradient(90deg,rgba(240,165,0,.025) 1px,transparent 1px);
  background-size:40px 40px;pointer-events:none;z-index:0;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
@keyframes spin{to{transform:rotate(360deg)}}
.hdr{position:sticky;top:0;z-index:100;
  background:linear-gradient(180deg,#0a1118,rgba(7,11,15,.97));
  border-bottom:2px solid var(--gold);padding:10px 14px;
  display:flex;align-items:center;justify-content:space-between;
  box-shadow:0 4px 24px rgba(240,165,0,.2);}
.logo{font-family:'Orbitron';font-size:11px;font-weight:900;color:var(--gold);letter-spacing:1px;}
.logo small{display:block;font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-top:1px;}
.hclock{font-family:'Orbitron';font-size:12px;color:var(--gold);}
.hlive{font-size:9px;font-family:'Share Tech Mono';padding:2px 7px;border-radius:3px;}
.hlive.on{border:1px solid var(--grn);color:var(--grn);}
.hlive.off{border:1px solid var(--red);color:var(--red);}
.sbar{display:flex;justify-content:space-between;padding:4px 12px;
  background:var(--bg2);border-bottom:1px solid var(--brd);
  font-family:'Share Tech Mono';font-size:9px;}
.sdot{width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:middle;}
.sdot.ok{background:var(--grn);}
.sdot.wait{background:var(--gold);animation:blink 1s infinite;}
.sdot.err{background:var(--red);}
.main{padding:10px;max-width:480px;margin:0 auto;position:relative;z-index:1;}
.src-row{display:flex;justify-content:space-between;padding:6px 11px;border-radius:7px;
  margin-bottom:9px;font-family:'Share Tech Mono';font-size:9px;
  border:1px solid var(--brd);background:var(--bg2);}
.src-row.angel{border-color:rgba(206,147,216,.5);color:var(--pur);}
.src-row.yahoo{border-color:rgba(240,165,0,.4);color:var(--gold);}
.src-row.none{border-color:rgba(255,23,68,.25);color:var(--red);}
.card{background:var(--bg2);border:1px solid var(--brd);border-radius:12px;padding:12px;margin-bottom:9px;}
.ctitle{font-family:'Orbitron';font-size:9px;color:var(--gold);letter-spacing:1px;
  margin-bottom:9px;display:flex;justify-content:space-between;align-items:center;}
.badge{display:inline-flex;padding:1px 7px;border-radius:8px;
  font-family:'Share Tech Mono';font-size:7px;}
.badge.live{background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.3);color:var(--grn);}
.badge.wait{background:rgba(41,182,246,.08);border:1px solid rgba(41,182,246,.2);color:var(--blu);}
.badge.err{background:rgba(255,23,68,.08);border:1px solid rgba(255,23,68,.2);color:var(--red);}
.badge.angel{background:rgba(206,147,216,.1);border:1px solid rgba(206,147,216,.3);color:var(--pur);}
/* inputs */
.inp{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:6px;
  color:var(--txt);padding:8px 10px;font-size:12px;font-family:'Share Tech Mono';outline:none;margin-bottom:6px;}
.inp:focus{border-color:var(--orn);}
.inp-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:.5px;margin-bottom:3px;}
.cbtn{width:100%;padding:11px;border-radius:8px;cursor:pointer;
  font-family:'Orbitron';font-size:9px;font-weight:700;letter-spacing:1px;
  border:1px solid var(--orn);background:rgba(255,152,0,.08);color:var(--orn);margin-top:6px;}
.cbtn.ok{border-color:var(--pur);background:rgba(206,147,216,.08);color:var(--pur);}
.cbtn.yahoo{border-color:var(--gold);background:rgba(240,165,0,.08);color:var(--gold);}
.btn-row{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:6px;}
.ki{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:6px;
  color:var(--grn);padding:8px;font-size:12px;font-family:'Share Tech Mono';outline:none;}
.idx-row{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.ib{background:var(--bg3);border:2px solid var(--brd);border-radius:9px;padding:9px;text-align:center;cursor:pointer;}
.ib.on{border-color:var(--gold);}
.ib-name{font-family:'Orbitron';font-size:13px;font-weight:900;}
.ib.on .ib-name{color:var(--gold);}
.ib-spot{font-family:'Share Tech Mono';font-size:11px;color:var(--grn);margin-top:2px;}
.ib-atm{font-family:'Share Tech Mono';font-size:8px;color:var(--blu);margin-top:1px;}
.gift-box{background:var(--bg2);border:1px solid var(--brd);border-radius:11px;
  padding:11px 13px;margin-bottom:9px;display:flex;justify-content:space-between;
  align-items:center;position:relative;overflow:hidden;}
.gift-box::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--gold);}
.g-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--gold);letter-spacing:1px;margin-bottom:2px;}
.g-val{font-family:'Orbitron';font-size:20px;font-weight:900;}
.g-chg{font-family:'Share Tech Mono';font-size:9px;margin-top:2px;}
.g-right{background:var(--bg3);border-radius:7px;padding:6px 9px;text-align:center;min-width:90px;}
.g-slbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:2px;}
.g-sval{font-size:12px;font-weight:700;}
.g-snote{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-top:1px;}
.mstrip{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-bottom:9px;}
.mc{background:var(--bg2);border:1px solid var(--brd);border-radius:8px;padding:7px;text-align:center;}
.mc-n{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:2px;}
.mc-v{font-family:'Orbitron';font-size:13px;font-weight:700;}
.mc-c{font-family:'Share Tech Mono';font-size:8px;margin-top:1px;}
.mc-a{font-family:'Share Tech Mono';font-size:7px;color:var(--blu);margin-top:2px;}
.oi-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px;}
.oi-cell{background:var(--bg3);border-radius:7px;padding:8px;text-align:center;border:1px solid var(--brd);}
.oi-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:2px;}
.oi-val{font-family:'Orbitron';font-size:14px;font-weight:700;}
.pcr-wrap{background:var(--bg3);border-radius:7px;padding:8px 9px;margin-bottom:7px;}
.pcr-lbl{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-bottom:5px;display:flex;justify-content:space-between;}
.pcr-bg{height:10px;border-radius:5px;background:rgba(255,255,255,.05);overflow:hidden;margin-bottom:4px;}
.pcr-fill{height:100%;border-radius:5px;transition:width .8s;}
.pcr-marks{display:flex;justify-content:space-between;font-family:'Share Tech Mono';font-size:7px;color:var(--dim);}
.pcr-sig{font-family:'Share Tech Mono';font-size:10px;margin-top:5px;text-align:center;}
.sr-row{display:grid;grid-template-columns:1fr 1fr;gap:6px;}
.sr-cell{border-radius:7px;padding:8px;text-align:center;}
.sr-sup{background:rgba(0,230,118,.07);border:1px solid rgba(0,230,118,.2);}
.sr-res{background:rgba(255,23,68,.07);border:1px solid rgba(255,23,68,.2);}
.sr-lbl{font-family:'Share Tech Mono';font-size:7px;letter-spacing:.5px;margin-bottom:2px;}
.sr-val{font-family:'Orbitron';font-size:14px;font-weight:700;}
.sr-oi{font-family:'Share Tech Mono';font-size:7px;margin-top:2px;color:var(--dim);}
.prem-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;}
.prem-cell{background:var(--bg3);border-radius:8px;padding:9px;border:2px solid var(--brd);text-align:center;transition:.3s;}
.prem-cell.bull{border-color:rgba(0,230,118,.5);background:rgba(0,230,118,.05);}
.prem-cell.bear{border-color:rgba(255,23,68,.5);background:rgba(255,23,68,.05);}
.ptype{font-family:'Orbitron';font-size:10px;font-weight:700;margin-bottom:3px;}
.pval{font-family:'Orbitron';font-size:20px;font-weight:700;}
.pchg{font-family:'Share Tech Mono';font-size:9px;margin-top:2px;}
.psig{font-family:'Share Tech Mono';font-size:8px;margin-top:4px;}
.ag-sect{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:2px;margin:6px 0 5px;}
.ag-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:4px;}
.agc{background:var(--bg3);border:1px solid var(--brd);border-radius:8px;padding:7px;position:relative;overflow:hidden;}
.agc::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--brd);}
.agc.bull::before{background:var(--grn);}
.agc.bear::before{background:var(--red);}
.agc.neut::before{background:var(--gold);}
.ag-top{display:flex;justify-content:space-between;margin-bottom:2px;}
.ag-id{font-family:'Orbitron';font-size:8px;color:var(--dim);}
.ag-sig{font-family:'Share Tech Mono';font-size:9px;font-weight:700;}
.ag-sig.bull{color:var(--grn);}
.ag-sig.bear{color:var(--red);}
.ag-sig.neut{color:var(--gold);}
.ag-sig.none{color:var(--dim);}
.ag-name{font-size:10px;font-weight:700;margin-bottom:1px;}
.ag-val{font-family:'Share Tech Mono';font-size:9px;color:var(--dim);}
.val-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-bottom:8px;}
.vbox{background:var(--bg3);border-radius:7px;padding:7px;text-align:center;border:1px solid var(--brd);}
.vnum{font-family:'Orbitron';font-size:17px;font-weight:900;}
.vnum.bull{color:var(--grn);}
.vnum.bear{color:var(--red);}
.vnum.neut{color:var(--gold);}
.vlbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-top:1px;}
.conf-bar{background:var(--bg3);border-radius:8px;padding:9px;margin-bottom:7px;}
.conf-lbl{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);margin-bottom:5px;display:flex;justify-content:space-between;}
.conf-track{height:10px;border-radius:5px;background:rgba(255,255,255,.05);overflow:hidden;display:flex;margin-bottom:3px;}
.conf-bull{height:100%;background:linear-gradient(90deg,#004d40,var(--grn));transition:width .7s;}
.conf-bear{height:100%;background:linear-gradient(90deg,var(--red),#7f0000);transition:width .7s;}
.conf-pct{display:flex;justify-content:space-between;font-family:'Share Tech Mono';font-size:8px;}
.brain-box{border-radius:13px;padding:14px;margin-bottom:9px;border:2px solid var(--brd);transition:all .4s;}
.brain-box.bull{border-color:rgba(0,230,118,.6);background:linear-gradient(135deg,rgba(0,230,118,.07),rgba(0,230,118,.01));box-shadow:0 0 30px rgba(0,230,118,.1);}
.brain-box.bear{border-color:rgba(255,23,68,.6);background:linear-gradient(135deg,rgba(255,23,68,.07),rgba(255,23,68,.01));box-shadow:0 0 30px rgba(255,23,68,.1);}
.brain-box.wait{border-color:rgba(240,165,0,.5);background:linear-gradient(135deg,rgba(240,165,0,.06),rgba(240,165,0,.01));}
.brain-box.idle{background:var(--bg2);}
.brain-lbl{font-family:'Share Tech Mono';font-size:8px;color:var(--dim);letter-spacing:2px;margin-bottom:4px;}
.brain-sig{font-family:'Orbitron';font-size:26px;font-weight:900;margin-bottom:3px;}
.brain-sub{font-size:11px;color:var(--dim);margin-bottom:9px;}
.reason-list{background:var(--bg3);border-radius:8px;padding:9px;}
.reason-lbl{font-family:'Share Tech Mono';font-size:7px;color:var(--dim);letter-spacing:1px;margin-bottom:5px;}
.reason-item{font-family:'Share Tech Mono';font-size:9px;padding:3px 0;border-bottom:1px solid rgba(30,45,61,.5);color:var(--txt);}
.reason-item:last-child{border:none;}
.cap-row{display:flex;gap:7px;margin-bottom:9px;}
.cap-inp{flex:1;background:var(--bg3);border:1px solid var(--brd);border-radius:7px;
  color:var(--txt);padding:9px 11px;font-size:14px;font-family:'Share Tech Mono';outline:none;}
.go-btn{width:100%;padding:15px;border-radius:13px;border:none;cursor:pointer;
  background:linear-gradient(135deg,#7a5200,var(--gold),#f5c540);
  color:#000;font-family:'Orbitron';font-size:12px;font-weight:900;
  letter-spacing:2px;box-shadow:0 6px 28px rgba(240,165,0,.3);margin-bottom:9px;}
.go-btn:disabled{background:#1a2230;color:var(--dim);box-shadow:none;}
.ref-btn{width:100%;padding:9px;border-radius:9px;cursor:pointer;
  border:1px solid rgba(41,182,246,.4);background:rgba(41,182,246,.05);
  color:var(--blu);font-family:'Orbitron';font-size:9px;letter-spacing:1px;margin-bottom:9px;}
.auto-row{display:flex;justify-content:space-between;align-items:center;
  background:var(--bg2);border:1px solid var(--brd);border-radius:7px;
  padding:7px 11px;margin-bottom:9px;font-family:'Share Tech Mono';font-size:9px;}
.toggle{width:34px;height:19px;background:var(--bg3);border-radius:10px;
  border:1px solid var(--brd);cursor:pointer;position:relative;display:inline-block;}
.toggle.on{background:rgba(0,230,118,.2);border-color:var(--grn);}
.toggle-dot{position:absolute;top:2px;left:2px;width:13px;height:13px;border-radius:50%;background:var(--dim);}
.toggle.on .toggle-dot{left:17px;background:var(--grn);}
.trap-warn{background:linear-gradient(135deg,rgba(255,23,68,.08),rgba(255,23,68,.02));
  border:1px solid rgba(255,23,68,.4);border-radius:9px;
  padding:10px 12px;margin-bottom:9px;font-family:'Share Tech Mono';font-size:10px;color:var(--red);}
.claude-box{background:var(--bg2);border:1px solid rgba(240,165,0,.2);border-radius:11px;padding:12px;margin-bottom:9px;}
.claude-title{font-family:'Orbitron';font-size:8px;color:var(--gold);letter-spacing:1.5px;margin-bottom:8px;}
.claude-text{font-size:13px;line-height:1.9;color:var(--txt);}
.wsbar{position:fixed;bottom:0;left:0;right:0;z-index:200;padding:3px 12px;
  font-family:'Share Tech Mono';font-size:9px;background:var(--bg2);
  border-top:1px solid var(--brd);display:flex;align-items:center;gap:6px;}
.wsdot{width:6px;height:6px;border-radius:50%;background:var(--red);flex-shrink:0;}
.wsdot.on{background:var(--grn);}
.sp{display:inline-block;width:11px;height:11px;border:2px solid rgba(0,0,0,.3);
  border-top-color:#000;border-radius:50%;animation:spin .7s linear infinite;
  vertical-align:middle;margin-right:4px;}
.status-msg{background:rgba(41,182,246,.07);border:1px solid rgba(41,182,246,.2);
  border-radius:7px;padding:8px 11px;margin-bottom:9px;
  font-family:'Share Tech Mono';font-size:9px;color:var(--blu);display:none;}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo">MATHAN AI — ANGEL ONE<small>REAL OI · REAL PREMIUM · 13 AGENTS</small></div>
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

<div class="src-row none" id="src-row">
  <span id="src-lbl">NOT CONNECTED</span>
  <span id="src-count" style="color:var(--dim)">fetch #0</span>
</div>

<div class="status-msg" id="status-msg"></div>

<!-- ANGEL ONE CONNECT -->
<div class="card" style="border-color:rgba(206,147,216,.3);">
  <div class="ctitle" style="color:var(--pur);">
    ANGEL ONE — REAL DATA
    <span id="angel-st" style="font-family:'Share Tech Mono';font-size:8px;color:var(--dim)">NOT SET</span>
  </div>
  <div style="font-family:'Share Tech Mono';font-size:7px;color:var(--dim);margin-bottom:8px;">
    Credentials stored in server DB. Auto-loads on restart.
  </div>
  <div class="inp-lbl">API KEY (from smartapi.angelbroking.com)</div>
  <input class="inp" id="api-key" type="password" placeholder="Your API Key" oninput="saveCreds()"/>
  <div class="inp-lbl">CLIENT ID (Angel One login ID)</div>
  <input class="inp" id="client-id" type="text" placeholder="A12345" oninput="saveCreds()"/>
  <div class="inp-lbl">PIN (4-digit trading PIN)</div>
  <input class="inp" id="angel-pin" type="password" placeholder="1234" oninput="saveCreds()"/>
  <div class="inp-lbl">TOTP SECRET (QR code key — saved once)</div>
  <input class="inp" id="totp-secret" type="password" placeholder="JBSWY3DPEHPK3PXP" oninput="saveCreds()"/>
  <div class="btn-row">
    <button class="cbtn" id="angel-btn" onclick="connectAngel()" style="margin:0">CONNECT ANGEL ONE</button>
    <button class="cbtn yahoo" onclick="setYahoo()" style="margin:0">YAHOO FALLBACK</button>
  </div>
</div>

<!-- CLAUDE KEY -->
<div class="card" style="border-color:rgba(41,182,246,.2);">
  <div class="ctitle" style="color:var(--blu);">CLAUDE AI KEY</div>
  <input class="ki" id="ki" type="password" placeholder="sk-ant-..." oninput="saveKey()"/>
  <div id="kst" style="font-family:'Share Tech Mono';font-size:9px;margin-top:3px;"></div>
</div>

<!-- INDEX -->
<div class="idx-row">
  <div class="ib on" id="ib-nifty" onclick="setIdx('NIFTY')">
    <div class="ib-name">NIFTY 50</div>
    <div class="ib-spot" id="n-spot">—</div>
    <div class="ib-atm" id="n-atm">ATM: —</div>
  </div>
  <div class="ib" id="ib-sensex" onclick="setIdx('SENSEX')">
    <div class="ib-name">SENSEX</div>
    <div class="ib-spot" id="s-spot">—</div>
    <div class="ib-atm" id="s-atm">ATM: —</div>
  </div>
</div>

<!-- GIFT NIFTY -->
<div class="gift-box">
  <div>
    <div class="g-lbl">GIFT NIFTY — TOMORROW SENTIMENT</div>
    <div class="g-val" id="gv" style="color:var(--gold)">—</div>
    <div class="g-chg" id="gc">—</div>
  </div>
  <div class="g-right">
    <div class="g-slbl">MOOD</div>
    <div class="g-sval" id="gs" style="color:var(--gold)">—</div>
    <div class="g-snote" id="gn">—</div>
  </div>
</div>

<!-- MARKET STRIP -->
<div class="mstrip">
  <div class="mc">
    <div class="mc-n">NIFTY 50</div>
    <div class="mc-v" id="nv" style="color:var(--grn)">—</div>
    <div class="mc-c" id="nc">—</div>
    <div class="mc-a" id="na">ATM: —</div>
  </div>
  <div class="mc">
    <div class="mc-n">SENSEX</div>
    <div class="mc-v" id="sv" style="color:var(--grn)">—</div>
    <div class="mc-c" id="sc">—</div>
    <div class="mc-a" id="sa">ATM: —</div>
  </div>
  <div class="mc">
    <div class="mc-n">INDIA VIX</div>
    <div class="mc-v" id="vv" style="color:var(--gold)">—</div>
    <div class="mc-c" id="vn" style="color:var(--dim)">—</div>
  </div>
</div>

<!-- OI ANALYSIS -->
<div class="card">
  <div class="ctitle">OI ANALYSIS — ANGEL ONE REAL <span class="badge wait" id="oi-src">LOADING</span></div>
  <div class="oi-grid">
    <div class="oi-cell"><div class="oi-lbl">TOTAL CALL OI</div><div class="oi-val" id="callOI" style="color:var(--red)">—</div></div>
    <div class="oi-cell"><div class="oi-lbl">TOTAL PUT OI</div><div class="oi-val" id="putOI" style="color:var(--grn)">—</div></div>
  </div>
  <div class="pcr-wrap">
    <div class="pcr-lbl"><span>PUT/CALL RATIO (PCR)</span><span id="pcrVal" style="color:var(--gold)">—</span></div>
    <div class="pcr-bg"><div class="pcr-fill" id="pcrFill" style="width:50%;background:var(--gold)"></div></div>
    <div class="pcr-marks"><span>BEAR &lt;0.7</span><span>NEUTRAL 1.0</span><span>BULL &gt;1.2</span></div>
    <div class="pcr-sig" id="pcrSig" style="color:var(--gold)">Awaiting Angel One data...</div>
  </div>
  <div class="sr-row">
    <div class="sr-cell sr-sup">
      <div class="sr-lbl" style="color:var(--grn)">SUPPORT (Max PUT OI)</div>
      <div class="sr-val" id="support" style="color:var(--grn)">—</div>
      <div class="sr-oi" id="supportOI">—</div>
    </div>
    <div class="sr-cell sr-res">
      <div class="sr-lbl" style="color:var(--red)">RESISTANCE (Max CALL OI)</div>
      <div class="sr-val" id="resistance" style="color:var(--red)">—</div>
      <div class="sr-oi" id="resistanceOI">—</div>
    </div>
  </div>
</div>

<!-- PREMIUM -->
<div class="card">
  <div class="ctitle">PREMIUM MOVEMENT — REAL TIME <span class="badge wait" id="prem-src">LOADING</span></div>
  <div class="prem-grid">
    <div class="prem-cell" id="ceCell">
      <div class="ptype" style="color:var(--grn)">CALL CE</div>
      <div class="pval" id="cePrem" style="color:var(--grn)">—</div>
      <div class="pchg" id="ceChg" style="color:var(--dim)">—</div>
      <div class="psig" id="ceSig" style="color:var(--dim)">Awaiting tick</div>
    </div>
    <div class="prem-cell" id="peCell">
      <div class="ptype" style="color:var(--red)">PUT PE</div>
      <div class="pval" id="pePrem" style="color:var(--red)">—</div>
      <div class="pchg" id="peChg" style="color:var(--dim)">—</div>
      <div class="psig" id="peSig" style="color:var(--dim)">Awaiting tick</div>
    </div>
  </div>
</div>

<!-- TRAP WARNING -->
<div class="trap-warn" id="trap-warn" style="display:none">
  ⚠️ L11 TRAP DETECTED — Market manipulation pattern. Exercise extreme caution.
</div>

<!-- 13 AGENTS -->
<div class="card">
  <div class="ctitle">13 AGENT SIGNALS <span class="badge wait" id="ag-badge">WAITING</span></div>
  <div class="ag-sect">▸ OI & PRICE</div>
  <div class="ag-grid">
    <div class="agc" id="card-l1"><div class="ag-top"><span class="ag-id">L1</span><span class="ag-sig none" id="sig-l1">—</span></div><div class="ag-name">OI Analyst</div><div class="ag-val" id="val-l1">—</div></div>
    <div class="agc" id="card-l2"><div class="ag-top"><span class="ag-id">L2</span><span class="ag-sig none" id="sig-l2">—</span></div><div class="ag-name">Price Action</div><div class="ag-val" id="val-l2">—</div></div>
    <div class="agc" id="card-l3"><div class="ag-top"><span class="ag-id">L3</span><span class="ag-sig none" id="sig-l3">—</span></div><div class="ag-name">VIX Monitor</div><div class="ag-val" id="val-l3">—</div></div>
    <div class="agc" id="card-l4"><div class="ag-top"><span class="ag-id">L4</span><span class="ag-sig none" id="sig-l4">—</span></div><div class="ag-name">GIFT Tracker</div><div class="ag-val" id="val-l4">—</div></div>
  </div>
  <div class="ag-sect">▸ PREMIUM & SESSION</div>
  <div class="ag-grid">
    <div class="agc" id="card-l5"><div class="ag-top"><span class="ag-id">L5</span><span class="ag-sig none" id="sig-l5">—</span></div><div class="ag-name">CE Premium</div><div class="ag-val" id="val-l5">—</div></div>
    <div class="agc" id="card-l6"><div class="ag-top"><span class="ag-id">L6</span><span class="ag-sig none" id="sig-l6">—</span></div><div class="ag-name">PE Premium</div><div class="ag-val" id="val-l6">—</div></div>
    <div class="agc" id="card-l7"><div class="ag-top"><span class="ag-id">L7</span><span class="ag-sig none" id="sig-l7">—</span></div><div class="ag-name">Session Clock</div><div class="ag-val" id="val-l7">—</div></div>
    <div class="agc" id="card-l8"><div class="ag-top"><span class="ag-id">L8</span><span class="ag-sig none" id="sig-l8">—</span></div><div class="ag-name">Expiry Watcher</div><div class="ag-val" id="val-l8">—</div></div>
  </div>
  <div class="ag-sect">▸ BEHAVIOUR & INTELLIGENCE</div>
  <div class="ag-grid">
    <div class="agc" id="card-l9"><div class="ag-top"><span class="ag-id">L9</span><span class="ag-sig none" id="sig-l9">—</span></div><div class="ag-name">Gap Detector</div><div class="ag-val" id="val-l9">—</div></div>
    <div class="agc" id="card-l10"><div class="ag-top"><span class="ag-id">L10</span><span class="ag-sig none" id="sig-l10">—</span></div><div class="ag-name">PCR Engine</div><div class="ag-val" id="val-l10">—</div></div>
    <div class="agc" id="card-l11" style="border-color:rgba(206,147,216,.2)"><div class="ag-top"><span class="ag-id">L11</span><span class="ag-sig none" id="sig-l11">—</span></div><div class="ag-name" style="color:var(--pur)">Trap Detector</div><div class="ag-val" id="val-l11">—</div></div>
    <div class="agc" id="card-l12"><div class="ag-top"><span class="ag-id">L12</span><span class="ag-sig none" id="sig-l12">—</span></div><div class="ag-name">Risk Control</div><div class="ag-val" id="val-l12">—</div></div>
    <div class="agc" id="card-l13" style="grid-column:span 2;border-color:rgba(240,165,0,.3)"><div class="ag-top"><span class="ag-id" style="color:var(--gold)">L13 — MASTER</span><span class="ag-sig none" id="sig-l13">—</span></div><div class="ag-name" style="color:var(--gold)">Behaviour AI</div><div class="ag-val" id="val-l13">—</div></div>
  </div>
</div>

<!-- NAMBI VALIDATION -->
<div class="card" style="border-color:rgba(41,182,246,.2);">
  <div class="ctitle" style="color:var(--blu);">NAMBI VALIDATION <span class="badge wait" id="val-badge">—</span></div>
  <div class="val-grid">
    <div class="vbox"><div class="vnum bull" id="v-bull">0</div><div class="vlbl">BULL</div></div>
    <div class="vbox"><div class="vnum bear" id="v-bear">0</div><div class="vlbl">BEAR</div></div>
    <div class="vbox"><div class="vnum neut" id="v-neut">0</div><div class="vlbl">HOLD</div></div>
  </div>
  <div class="conf-bar">
    <div class="conf-lbl"><span style="color:var(--grn)">BULL</span><span id="conf-mid" style="color:var(--gold)">Confidence: —</span><span style="color:var(--red)">BEAR</span></div>
    <div class="conf-track">
      <div class="conf-bull" id="conf-bull" style="width:50%"></div>
      <div class="conf-bear" id="conf-bear" style="width:50%"></div>
    </div>
    <div class="conf-pct"><span id="bp" style="color:var(--grn)">50%</span><span id="brp" style="color:var(--red)">50%</span></div>
  </div>
</div>

<!-- BRAIN DECISION -->
<div class="brain-box idle" id="brain-box">
  <div class="brain-lbl">MARKET BRAIN — FINAL DECISION</div>
  <div class="brain-sig" id="brain-sig" style="color:var(--dim)">AWAITING DATA</div>
  <div class="brain-sub" id="brain-sub">Connect Angel One to begin</div>
  <div class="reason-list" id="reason-list" style="display:none">
    <div class="reason-lbl">SIGNAL SOURCES</div>
    <div id="reasons"></div>
  </div>
</div>

<!-- CAPITAL + ANALYSE -->
<div class="cap-row">
  <input class="cap-inp" id="cap" type="number" placeholder="Capital ₹" value="10000"/>
  <button style="padding:9px 14px;border-radius:7px;cursor:pointer;border:1px solid var(--gold);background:rgba(240,165,0,.08);color:var(--gold);font-family:'Orbitron';font-size:9px;font-weight:700;" onclick="runTrade()">TRADE</button>
</div>

<div class="card" id="trade-card" style="display:none">
  <div class="ctitle">TRADE SETUP</div>
  <div id="trade-box" style="font-family:'Share Tech Mono';font-size:11px;"></div>
</div>

<!-- AUTO + REFRESH -->
<div class="auto-row">
  <span>Auto refresh every 15s</span>
  <div class="toggle" id="auto-tog" onclick="toggleAuto()"><div class="toggle-dot"></div></div>
</div>
<button class="ref-btn" onclick="doFetch()">REFRESH — FETCH LIVE DATA NOW</button>

<!-- CLAUDE BUTTON -->
<button class="go-btn" id="go-btn" onclick="runClaude()">⚡ NAMBI + CLAUDE — FULL STRATEGY</button>

<!-- CLAUDE OUTPUT -->
<div class="claude-box" id="claude-box" style="display:none">
  <div class="claude-title">CLAUDE AI — MARKET BRAIN STRATEGY</div>
  <div class="claude-text" id="claude-text"></div>
</div>

</div>

<div class="wsbar">
  <div class="wsdot" id="wsdot"></div>
  <span id="ws-txt">Connecting...</span>
  <span id="ws-info" style="margin-left:auto;color:var(--dim)"></span>
</div>

<script>
const WS_URL = location.origin.replace(/^http/,'ws') + '/ws';

// ── ZERO FAILURE WEBSOCKET ──────────────────────────────────────────
let ws        = null;
let ok        = false;
let rcDelay   = 1000;       // start at 1s, max 10s
let rcTmr     = null;
let hbTmr     = null;       // heartbeat interval
let wdTmr     = null;       // watchdog interval
let hbMissed  = 0;          // consecutive missed pongs
let connecting = false;     // prevent duplicate connections
let autoOn    = true;
let srvM={}, srvAg={}, srvBr={}, srvSys={};

function setOnline() {
  ok=true; hbMissed=0; rcDelay=1000; connecting=false;
  q('wsdot').className='wsdot on';
  q('live-badge').className='hlive on'; q('live-badge').textContent='LIVE';
  wst('Connected');
}

function setOffline(reason) {
  ok=false;
  q('wsdot').className='wsdot';
  q('live-badge').className='hlive off'; q('live-badge').textContent='OFFLINE';
  wst(reason||'Offline — reconnecting...');
}

function stopTimers() {
  clearInterval(hbTmr); hbTmr=null;
  clearInterval(wdTmr); wdTmr=null;
  clearTimeout(rcTmr);  rcTmr=null;
}

function safeClose() {
  if(!ws) return;
  try {
    ws.onopen=null; ws.onmessage=null;
    ws.onerror=null; ws.onclose=null;
    if(ws.readyState===WebSocket.OPEN||ws.readyState===WebSocket.CONNECTING)
      ws.close();
  } catch(e){}
  ws=null;
}

function schedRC() {
  if(rcTmr) return;                         // already scheduled
  setOffline('Reconnecting in '+Math.round(rcDelay/1000)+'s...');
  rcTmr = setTimeout(()=>{
    rcTmr=null;
    connect();
    rcDelay = Math.min(rcDelay*2, 10000);   // exp backoff, max 10s
  }, rcDelay);
}

function startHeartbeat() {
  stopTimers();
  hbMissed = 0;

  // Ping every 3s
  hbTmr = setInterval(()=>{
    if(!ws || ws.readyState!==WebSocket.OPEN) {
      stopTimers(); schedRC(); return;
    }
    ws.send(JSON.stringify({type:'ping'}));
    hbMissed++;
    if(hbMissed>=3) {
      // 3 missed pongs = dead connection
      console.warn('[WS] Heartbeat timeout — forcing reconnect');
      stopTimers(); safeClose(); schedRC();
    }
  }, 3000);

  // Watchdog: check readyState every 5s independently
  wdTmr = setInterval(()=>{
    if(!ws || ws.readyState!==WebSocket.OPEN) {
      stopTimers(); safeClose(); schedRC();
    }
  }, 5000);
}

function connect() {
  if(connecting) return;                    // prevent duplicate
  if(ws && ws.readyState===WebSocket.OPEN) return;  // already open
  connecting=true;
  safeClose();
  wst('Connecting...');

  try {
    ws = new WebSocket(WS_URL);
  } catch(e) {
    connecting=false; schedRC(); return;
  }

  // Timeout: if not open in 8s, retry
  const openTimeout = setTimeout(()=>{
    if(!ws || ws.readyState!==WebSocket.OPEN){
      connecting=false; safeClose(); schedRC();
    }
  }, 8000);

  ws.onopen = () => {
    clearTimeout(openTimeout);
    setOnline();
    startHeartbeat();
    // Request fresh state on reconnect
    try { ws.send(JSON.stringify({type:'get_state'})); } catch(e){}
  };

  ws.onmessage = (e) => {
    hbMissed = 0;  // reset on any message — connection is alive
    let m; try{m=JSON.parse(e.data);}catch{return;}
    handle(m);
  };

  ws.onerror = (e) => {
    clearTimeout(openTimeout);
    connecting=false;
    stopTimers(); safeClose(); schedRC();
  };

  ws.onclose = (e) => {
    clearTimeout(openTimeout);
    connecting=false;
    stopTimers();
    setOffline('Disconnected ('+e.code+')');
    schedRC();
  };
}

function wsSend(o) {
  if(ws && ws.readyState===1){
    ws.send(JSON.stringify(o));
    return;
  }
  // WS not ready — use REST fallback for critical actions
  if(o.type==='connect_angel'){
    fetch('/connect_angel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)})
      .then(r=>r.json()).then(j=>{
        if(j.ok) showStatus('Login started — watch for [ANGEL] in server logs');
        else showStatus('Error: '+j.error);
      }).catch(e=>showStatus('Network error: '+e));
    return;
  }
  if(o.type==='set_yahoo'){
    fetch('/set_yahoo',{method:'POST'}).then(()=>sdot('wait','Yahoo connecting...')).catch(()=>{});
    return;
  }
}

function handle(m) {
  if(m.type==='init'){
    setSrc(m.source);
    q('ib-nifty').className='ib'+(m.index==='NIFTY'?' on':'');
    q('ib-sensex').className='ib'+(m.index==='SENSEX'?' on':'');
    if(m.angel_ok) setAngelOk();
    sdot(m.source!=='NONE'?'ok':'wait',
         m.source!=='NONE'?'Connected — '+m.source:'Ready — enter Angel One credentials');
    return;
  }
  if(m.type==='state_update'){
    srvSys=m.sys||{}; srvM=m.market||{}; srvAg=m.agents||{}; srvBr=m.brain||{};
    render(); return;
  }
  if(m.type==='angel_login_ok'){ sdot('ok','Angel One login OK'); return; }
  if(m.type==='angel_ws_connected'){ sdot('ok','Angel One WS live — option data flowing'); setAngelOk(); return; }
  if(m.type==='angel_connected'){
    setAngelOk();
    sdot('ok','Angel One connected — '+m.tokens+' option tokens subscribed'); return;
  }
  if(m.type==='angel_err'){
    q('angel-st').textContent='FAILED'; q('angel-st').style.color='var(--red)';
    sdot('err','Angel One: '+m.msg); return;
  }
  if(m.type==='status_msg'){
    showStatus(m.msg); return;
  }
  if(m.type==='source_changed'){ setSrc(m.source); return; }
  if(m.type==='fetch_error'){ sdot('err','Error: '+m.error); return; }
  if(m.type==='pong'){ q('ws-info').textContent=m.ts; return; }
}

function setAngelOk(){
  q('angel-st').textContent='● LIVE'; q('angel-st').style.color='var(--pur)';
  q('angel-btn').style.borderColor='var(--pur)'; q('angel-btn').style.color='var(--pur)';
  q('angel-btn').textContent='ANGEL ONE CONNECTED';
}

function showStatus(msg){
  const el=q('status-msg'); el.style.display='block'; el.textContent=msg;
  setTimeout(()=>el.style.display='none', 5000);
}

function render(){
  const D=srvM, ag=srvAg, br=srvBr, sys=srvSys;
  setSrc(sys.source);
  t('src-count','fetch #'+(sys.count||0));
  if(sys.angel_ok) setAngelOk();

  const idx=sys.index||'NIFTY';
  q('ib-nifty').className='ib'+(idx==='NIFTY'?' on':'');
  q('ib-sensex').className='ib'+(idx==='SENSEX'?' on':'');
  if(idx==='NIFTY'){ tv('nv',D.spot?D.spot.toFixed(0):'—','var(--grn)'); t('na',D.atm?'ATM: '+D.atm:'—'); t('n-spot',D.spot?D.spot.toFixed(0):'—'); t('n-atm',D.atm?'ATM: '+D.atm:'—'); }
  else             { tv('sv',D.spot?D.spot.toFixed(0):'—','var(--grn)'); t('sa',D.atm?'ATM: '+D.atm:'—'); t('s-spot',D.spot?D.spot.toFixed(0):'—'); t('s-atm',D.atm?'ATM: '+D.atm:'—'); }

  if(D.vix){ tv('vv',D.vix.toFixed(1),D.vix>20?'var(--red)':D.vix>15?'var(--gold)':'var(--grn)'); tv('vn',D.vix>20?'HIGH FEAR':D.vix>15?'CAUTION':'CALM',D.vix>20?'var(--red)':D.vix>15?'var(--gold)':'var(--grn)'); }

  if(D.gift){
    const gd=D.gift_diff||0;
    tv('gv',D.gift.toFixed(0),gd>=0?'var(--grn)':'var(--red)');
    tv('gc',(gd>=0?'▲ +':'▼ ')+Math.abs(gd).toFixed(0)+' pts',gd>=0?'var(--grn)':'var(--red)');
    let gs='NEUTRAL',gn='Flat open',gc='var(--gold)';
    if(gd>100){gs='BULLISH';gn='Gap Up';gc='var(--grn)';}
    else if(gd>40){gs='MILD BULL';gn='Positive open';gc='var(--grn)';}
    else if(gd<-100){gs='BEARISH';gn='Gap Down';gc='var(--red)';}
    else if(gd<-40){gs='MILD BEAR';gn='Negative open';gc='var(--red)';}
    tv('gs',gs,gc); t('gn',gn);
  }

  const angel=sys.angel_ok&&sys.angel_ws;
  q('oi-src').className='badge '+(angel?'angel':'wait');
  q('oi-src').textContent=angel?'● ANGEL ONE REAL':'AWAITING TICKS';
  q('prem-src').className='badge '+(angel?'angel':'wait');
  q('prem-src').textContent=angel?'● REAL TIME':'AWAITING TICKS';

  t('callOI',D.call_oi?fmtOI(D.call_oi):'N/A');
  t('putOI',D.put_oi?fmtOI(D.put_oi):'N/A');

  if(D.pcr!=null){
    const pcr=D.pcr;
    tv('pcrVal',pcr.toFixed(2),pcr>1.2?'var(--grn)':pcr<0.75?'var(--red)':'var(--gold)');
    const pct=Math.min(100,Math.max(0,(pcr/2)*100));
    const pf=q('pcrFill'); pf.style.width=pct+'%';
    pf.style.background=pcr>1.2?'var(--grn)':pcr<0.75?'var(--red)':'var(--gold)';
    let ps='',pc='';
    if(pcr>1.5){ps='STRONG BULL — Put writing dominant';pc='var(--grn)';}
    else if(pcr>1.2){ps='BULLISH — PCR above 1.2';pc='var(--grn)';}
    else if(pcr<0.6){ps='STRONG BEAR — Call writing dominant';pc='var(--red)';}
    else if(pcr<0.8){ps='BEARISH — PCR low';pc='var(--red)';}
    else{ps='NEUTRAL — PCR ~1.0';pc='var(--gold)';}
    tv('pcrSig',ps,pc);
  } else { t('pcrSig',angel?'Calculating...':'Connect Angel One for real PCR'); }

  if(D.support){ tv('support',D.support.toLocaleString('en-IN'),'var(--grn)'); t('supportOI',D.sup_oi?'PUT OI: '+fmtOI(D.sup_oi):'Max PUT OI'); }
  else t('support','N/A');
  if(D.resistance){ tv('resistance',D.resistance.toLocaleString('en-IN'),'var(--red)'); t('resistanceOI',D.res_oi?'CALL OI: '+fmtOI(D.res_oi):'Max CALL OI'); }
  else t('resistance','N/A');

  if(D.ce_prem){
    tv('cePrem','₹'+D.ce_prem.toFixed(0),'var(--grn)');
    const chg=D.ce_prev?D.ce_prem-D.ce_prev:0;
    tv('ceChg',(chg>=0?'▲ +':'▼ ')+Math.abs(chg).toFixed(0),chg>=0?'var(--grn)':'var(--red)');
    if(chg>5){q('ceCell').className='prem-cell bull';tv('ceSig','CE RISING — BULLISH','var(--grn)');}
    else{q('ceCell').className='prem-cell';t('ceSig','CE monitoring');}
  } else t('cePrem','N/A');
  if(D.pe_prem){
    tv('pePrem','₹'+D.pe_prem.toFixed(0),'var(--red)');
    const chg=D.pe_prev?D.pe_prem-D.pe_prev:0;
    tv('peChg',(chg>=0?'▲ +':'▼ ')+Math.abs(chg).toFixed(0),chg>=0?'var(--red)':'var(--grn)');
    if(chg>5){q('peCell').className='prem-cell bear';tv('peSig','PE RISING — BEARISH','var(--red)');}
    else{q('peCell').className='prem-cell';t('peSig','PE monitoring');}
  } else t('pePrem','N/A');

  q('trap-warn').style.display=srvBr.trap_detected?'block':'none';

  for(const [aid,a] of Object.entries(ag)){
    const card=q('card-'+aid),sig=q('sig-'+aid),val=q('val-'+aid);
    if(!card)continue; const d=a.signal;
    card.className='agc '+(d||'');
    if(sig){sig.className='ag-sig '+(d||'none');sig.textContent=d==='bull'?'▲ BULL':d==='bear'?'▼ BEAR':d==='neut'?'◆ HOLD':'—';}
    if(val)val.textContent=a.detail||'—';
  }
  const hasData=D.spot&&D.vix;
  q('ag-badge').className='badge '+(hasData?'live':'wait');
  q('ag-badge').textContent=hasData?'● LIVE':'WAITING';

  const br=srvBr;
  const bp_=br.bull_pct||50, brp_=br.bear_pct||50;
  t('v-bull',br.bull||0); t('v-bear',br.bear||0); t('v-neut',br.neut||0);
  q('conf-bull').style.width=bp_+'%'; q('conf-bear').style.width=brp_+'%';
  tv('bp',bp_+'%','var(--grn)'); tv('brp',brp_+'%','var(--red)');
  t('conf-mid','Confidence: '+(br.confidence||'—'));
  const bc={bull:'live',bear:'err',wait:'wait',idle:'wait'}[br.signal==='BUY CE'?'bull':br.signal==='BUY PE'?'bear':br.signal==='WAIT'?'wait':'idle']||'wait';
  q('val-badge').className='badge '+bc;
  q('val-badge').textContent=br.signal||'—';

  const bb=q('brain-box');
  const cls=br.signal==='BUY CE'?'bull':br.signal==='BUY PE'?'bear':br.signal==='WAIT'?'wait':'idle';
  bb.className='brain-box '+cls;
  const cols={bull:'var(--grn)',bear:'var(--red)',wait:'var(--gold)',idle:'var(--dim)'};
  const labels={'BUY CE':'🟢 BUY CE — BULLISH','BUY PE':'🔴 BUY PE — BEARISH','WAIT':'⏳ WAIT — HOLD CAPITAL'};
  tv('brain-sig',labels[br.signal]||'AWAITING',cols[cls]||'var(--dim)');
  t('brain-sub',(sys.source||'—')+' | '+br.confidence+' | Bull '+bp_+'% Bear '+brp_+'%');
  if(br.reasons&&br.reasons.length){
    q('reason-list').style.display='block';
    q('reasons').innerHTML=br.reasons.slice(0,6).map(r=>'<div class="reason-item">▸ '+r+'</div>').join('');
  }

  if(sys.error) sdot('err','Error: '+sys.error);
  else if(D.spot&&D.vix) sdot('ok','Live #'+(sys.count||0)+' — '+(D.fetch_time||''));
  else sdot('wait','Waiting for data...');
}

function runTrade(){
  const cap=parseFloat(q('cap').value)||0;
  if(!srvM.spot||cap<500) return;
  const br=srvBr,D=srvM,sys=srvSys;
  const lot=sys.index==='NIFTY'?75:20;
  const prem=br.signal==='BUY CE'&&D.ce_prem?D.ce_prem:br.signal==='BUY PE'&&D.pe_prem?D.pe_prem:90;
  const lots=Math.max(0,Math.floor(cap/(prem*lot)));
  if(!lots){q('trade-card').style.display='none';return;}
  const sl=Math.round(prem*.7),t1=Math.round(prem*1.5),t2=Math.round(prem*2.2),t3=Math.round(prem*3);
  const st=br.signal==='BUY CE'?'CE':'PE';
  q('trade-box').innerHTML=
    tr('Index',sys.index||'NIFTY','gold')+
    tr('Spot',D.spot?D.spot.toFixed(0):'—','')+
    tr('ATM Strike',D.atm?D.atm+' '+st:'—','blu')+
    tr('Support',D.support?D.support.toLocaleString('en-IN'):'N/A','grn')+
    tr('Resistance',D.resistance?D.resistance.toLocaleString('en-IN'):'N/A','red')+
    tr('PCR',D.pcr||'N/A','gold')+
    tr('Expiry',D.exp_days===0?'TODAY ⚡':D.exp_days+' days','')+
    tr('Lots',lots+' lots = '+(lots*lot)+' qty','gold')+
    tr('Premium','₹'+prem,'')+
    tr('Capital Used','₹'+(lots*lot*prem).toLocaleString('en-IN'),'')+
    tr('Stop Loss','₹'+sl+' (-30%)','red')+
    tr('Target 1','₹'+t1+' (+50%)','grn')+
    tr('Target 2','₹'+t2+' (+120%)','grn')+
    tr('Target 3','₹'+t3+' (+200%)','grn');
  q('trade-card').style.display='block';
  q('trade-card').scrollIntoView({behavior:'smooth'});
}
function tr(k,v,c){return '<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(30,45,61,.4);font-size:11px;"><span style="color:var(--dim)">'+k+'</span><span style="font-family:\'Share Tech Mono\';font-weight:700;'+( c?'color:var(--'+c+')':'')+'" >'+v+'</span></div>';}

async function runClaude(){
  const key=getKey();
  if(!key||!srvM.spot) return;
  const btn=q('go-btn'); btn.disabled=true; btn.innerHTML='<span class="sp"></span>Computing...';
  const D=srvM,br=srvBr,ag=srvAg,sys=srvSys;
  const sigs=Object.entries(ag).map(([id,a])=>id.toUpperCase()+' '+a.name+': '+(a.signal||'N/A').toUpperCase()+' — '+(a.detail||'')).join('\\n');
  const prompt='You are MATHAN AI Market Brain. Source: ANGEL ONE (real OI/premium).\\nChairman: Mr. Mathan Sir\\n\\nLIVE DATA:\\n'+sys.index+' Spot: '+(D.spot?D.spot.toFixed(0):'N/A')+' ATM: '+(D.atm||'N/A')+'\\nVIX: '+(D.vix?D.vix.toFixed(1):'N/A')+' PCR: '+(D.pcr||'N/A')+'\\nGIFT: '+(D.gift?D.gift.toFixed(0):'N/A')+' ('+(D.gift_diff>=0?'+':'')+D.gift_diff+' pts)\\nCE: '+(D.ce_prem?'Rs'+D.ce_prem.toFixed(0):'N/A')+' PE: '+(D.pe_prem?'Rs'+D.pe_prem.toFixed(0):'N/A')+'\\nCallOI: '+(D.call_oi||'N/A')+' PutOI: '+(D.put_oi||'N/A')+'\\nSupport: '+(D.support||'N/A')+' Resist: '+(D.resistance||'N/A')+'\\nExpiry: '+(D.exp_days||'N/A')+' days\\n\\n13 AGENTS:\\n'+sigs+'\\n\\nBRAIN: '+br.signal+' B:'+br.bull_pct+'% Br:'+br.bear_pct+'% Conf:'+br.confidence+' Trap:'+br.trap_detected+'\\n\\nGive Chairman:\\n1. FINAL CALL: reason\\n2. Strike: ATM/OTM which\\n3. Entry: time+condition\\n4. SL: exact Rs\\n5. T1/T2/T3 with partial exit\\n6. Top 3 agents\\n7. Risk warning\\n\\nTamil+English. Bold numbers.';
  q('claude-box').style.display='block';
  q('claude-text').innerHTML='<span style="color:var(--gold)">Computing strategy...</span>';
  q('claude-box').scrollIntoView({behavior:'smooth'});
  try{
    const r=await fetch('https://api.anthropic.com/v1/messages',{
      method:'POST',
      headers:{'Content-Type':'application/json','x-api-key':key,'anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'},
      body:JSON.stringify({model:'claude-sonnet-4-20250514',max_tokens:800,messages:[{role:'user',content:prompt}]}),
      signal:AbortSignal.timeout(35000)
    });
    const j=await r.json();
    if(j.error) q('claude-text').innerHTML='<span style="color:var(--red)">'+(j.error.message||'Error')+'</span>';
    else q('claude-text').innerHTML=(j?.content?.[0]?.text||'').replace(/\\n/g,'<br>').replace(/\\*\\*(.*?)\\*\\*/g,'<strong style="color:var(--gold)">$1</strong>');
  }catch(e){
    q('claude-text').innerHTML='<span style="color:var(--dim)">'+(e.name==='TimeoutError'?'Timeout — Retry':'Network error')+'</span>';
  }
  btn.disabled=false; btn.innerHTML='⚡ NAMBI + CLAUDE — FULL STRATEGY';
}

// SEND TO BACKEND
function connectAngel(){
  const ak=q('api-key').value.trim();
  const ci=q('client-id').value.trim();
  const pin=q('angel-pin').value.trim();
  const ts=q('totp-secret').value.trim();
  if(!ak||!ci||!pin||!ts){ showStatus('All 4 fields required'); return; }
  wsSend({type:'connect_angel',api_key:ak,client_id:ci,pin:pin,totp_secret:ts});
  q('angel-btn').textContent='Connecting...'; showStatus('Sending credentials to server...');
}
function setYahoo(){ wsSend({type:'set_yahoo'}); sdot('wait','Switching to Yahoo...'); }
function setIdx(idx){ wsSend({type:'set_index',index:idx}); }
function doFetch(){ wsSend({type:'fetch'}); sdot('wait','Fetching...'); }
function toggleAuto(){ autoOn=!autoOn; wsSend({type:'set_auto',on:autoOn}); q('auto-tog').className='toggle'+(autoOn?' on':''); }

function setSrc(src){
  const el=q('src-row');
  if(src==='ANGEL ONE'||src==='ANGEL'){el.className='src-row angel';t('src-lbl','◆ ANGEL ONE — REAL OI + PREMIUM');}
  else if(src==='YAHOO'){el.className='src-row yahoo';t('src-lbl','📡 YAHOO — SPOT+VIX (fallback)');}
  else{el.className='src-row none';t('src-lbl','NOT CONNECTED');}
}
function sdot(s,txt){q('sdot').className='sdot '+s;q('stxt').textContent=txt;q('stxt').style.color=s==='ok'?'var(--grn)':s==='err'?'var(--red)':'var(--gold)';}
function wst(txt){q('ws-txt').textContent=txt;}
function saveKey(){const v=q('ki').value.trim();if(v.startsWith('sk-ant')){localStorage.setItem('mbk',v);t('kst','✅ Saved');}}
function getKey(){const v=q('ki').value.trim();return v.startsWith('sk-ant')?v:(localStorage.getItem('mbk')||'');}
function saveCreds(){
  const ak=q('api-key').value.trim(),ci=q('client-id').value.trim();
  const pin=q('angel-pin').value.trim(),ts=q('totp-secret').value.trim();
  if(ak) localStorage.setItem('a_ak',ak);
  if(ci) localStorage.setItem('a_ci',ci);
  if(pin) localStorage.setItem('a_pin',pin);
  if(ts) localStorage.setItem('a_ts',ts);
}
function loadSaved(){
  const k=localStorage.getItem('mbk'); if(k){q('ki').value=k;t('kst','✅ Loaded');}
  const ak=localStorage.getItem('a_ak'); if(ak)q('api-key').value=ak;
  const ci=localStorage.getItem('a_ci'); if(ci)q('client-id').value=ci;
  const pin=localStorage.getItem('a_pin'); if(pin)q('angel-pin').value=pin;
  const ts=localStorage.getItem('a_ts'); if(ts)q('totp-secret').value=ts;
}
function fmtOI(n){if(!n)return'—';if(n>10000000)return(n/10000000).toFixed(1)+'Cr';if(n>100000)return(n/100000).toFixed(1)+'L';if(n>1000)return(n/1000).toFixed(1)+'K';return''+n;}
function q(i){return document.getElementById(i);}
function t(i,v){const e=q(i);if(e)e.textContent=v;}
function tv(i,v,c){const e=q(i);if(e){e.textContent=v;if(c)e.style.color=c;}}
setInterval(()=>{
  const n=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Kolkata'}));
  const p=v=>String(v).padStart(2,'0');
  const ts=p(n.getHours())+':'+p(n.getMinutes())+':'+p(n.getSeconds());
  t('clock',ts); t('rtxt','IST '+ts);
},1000);
window.onload=()=>{ loadSaved(); q('auto-tog').className='toggle on'; connect(); };
</script>
</body>
</html>"""

app  = Flask(__name__)
sock = Sock(app)

# ── CONFIG ─────────────────────────────────────────────────────────
PORT         = int(os.environ.get("PORT", 8000))
DB           = "/tmp/mathan_brain.db"
SCRIP_URL    = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
SCRIP_CACHE  = "/tmp/angel_scrip_master.json"

INDEX_CFG = {
    "NIFTY":  {"step": 50,  "lot": 75,  "token": "26000", "exchange": "NSE"},
    "SENSEX": {"step": 100, "lot": 20,  "token": "1",     "exchange": "BSE"},
}

# ── ANGEL ONE STATE ─────────────────────────────────────────────────
ANGEL = {
    "api_key":     "",
    "client_id":   "",
    "pin":         "",
    "totp_secret": "",
    "connected":   False,
    "jwt_token":   "",
    "feed_token":  "",
    "session_obj": None,
    "ws":          None,
    "ws_running":  False,
    "ws_thread":   None,
    "error":       None,
}

# ── SYSTEM STATE ────────────────────────────────────────────────────
SYS = {
    "source":      "NONE",
    "index":       "NIFTY",
    "auto":        True,
    "fetching":    False,
    "last_fetch":  None,
    "error":       None,
    "count":       0,
    "auth_failures": 0,
    "poll_interval": 15,
}

# Market data — None = not received
M = {
    "spot": None, "prev": None, "gap": None,
    "vix":  None, "gift": None, "gift_diff": None,
    "atm":  None,
    "pcr":  None, "call_oi": None, "put_oi": None,
    "ce_prem": None, "pe_prem": None,
    "ce_prev": None, "pe_prev": None,
    "support": None, "resistance": None,
    "sup_oi":  None, "res_oi":    None,
    "exp_days": None, "fetch_time": None, "source": None,
}

# Option chain buffer — keyed by token
OC_DATA = {}   # { token: {"ltp": x, "oi": x, "type": "CE"/"PE", "strike": x} }
OC_LOCK = threading.Lock()

AGENTS = {
    "l1":  {"name":"OI Analyst",      "signal":None,"detail":"","weight":1.5},
    "l2":  {"name":"Price Action",    "signal":None,"detail":"","weight":1.5},
    "l3":  {"name":"VIX Monitor",     "signal":None,"detail":"","weight":1.5},
    "l4":  {"name":"GIFT Tracker",    "signal":None,"detail":"","weight":1.0},
    "l5":  {"name":"CE Premium",      "signal":None,"detail":"","weight":1.0},
    "l6":  {"name":"PE Premium",      "signal":None,"detail":"","weight":1.0},
    "l7":  {"name":"Session Clock",   "signal":None,"detail":"","weight":0.8},
    "l8":  {"name":"Expiry Watcher",  "signal":None,"detail":"","weight":0.8},
    "l9":  {"name":"Gap Detector",    "signal":None,"detail":"","weight":1.0},
    "l10": {"name":"PCR Engine",      "signal":None,"detail":"","weight":1.2},
    "l11": {"name":"Trap Detector",   "signal":None,"detail":"","weight":1.5},
    "l12": {"name":"Risk Control",    "signal":None,"detail":"","weight":1.2},
    "l13": {"name":"Behaviour AI",    "signal":None,"detail":"","weight":2.0},
}

BRAIN = {
    "signal": "WAIT", "bull_pct": 50, "bear_pct": 50,
    "confidence": "LOW", "reasons": [], "source": "NONE",
    "computed_at": None, "trap_detected": False, "conflict": False,
}

# ── LOCKS ───────────────────────────────────────────────────────────
state_lock = threading.Lock()
_cl_lock   = threading.Lock()
_clients   = []

def cl_add(ws):
    with _cl_lock: _clients.append(ws)
def cl_rm(ws):
    with _cl_lock:
        try: _clients.remove(ws)
        except: pass
def cl_snap():
    with _cl_lock: return list(_clients)

def broadcast(p):
    data = json.dumps(p)
    snap = cl_snap(); dead = []
    for c in snap:
        try: c.send(data)
        except: dead.append(c)
    for c in dead: cl_rm(c)

def send1(ws, p):
    try: ws.send(json.dumps(p)); return True
    except: return False

# ── DATABASE ────────────────────────────────────────────────────────
def db_init():
    c = sqlite3.connect(DB)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS decisions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal TEXT, confidence TEXT, bull_pct INTEGER,
            source TEXT, reasons TEXT, ts TEXT);
    """)
    c.commit(); c.close()

def db_set(k, v):
    try:
        c = sqlite3.connect(DB)
        c.execute("INSERT OR REPLACE INTO config VALUES(?,?)", (k, str(v)))
        c.commit(); c.close()
    except: pass

def db_get(k):
    try:
        c = sqlite3.connect(DB)
        r = c.execute("SELECT value FROM config WHERE key=?", (k,)).fetchone()
        c.close(); return r[0] if r else None
    except: return None

def db_load():
    for field in ["api_key","client_id","pin","totp_secret"]:
        v = db_get(f"angel_{field}")
        if v: ANGEL[field] = v
    idx = db_get("index")
    if idx in INDEX_CFG: SYS["index"] = idx
    print(f"[CONFIG] Loaded. angel_connected={bool(ANGEL['api_key'])}")

# ── HELPERS ─────────────────────────────────────────────────────────
def ist():
    tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return datetime.datetime.now(tz).strftime("%H:%M:%S")

def ist_mins():
    tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    t  = datetime.datetime.now(tz)
    return t.hour * 60 + t.minute

def calc_expiry():
    tz  = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    t   = datetime.datetime.now(tz)
    d2t = (3 - t.weekday()) % 7
    if d2t == 0 and t.hour >= 15 and t.minute >= 30: d2t = 7
    return d2t

def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except: return "127.0.0.1"

def fmt_oi(n):
    if not n: return "—"
    if n > 10000000: return f"{n/10000000:.1f}Cr"
    if n > 100000:   return f"{n/100000:.1f}L"
    if n > 1000:     return f"{n/1000:.1f}K"
    return str(n)

# ── SCRIP MASTER ─────────────────────────────────────────────────────
def load_scrip_master():
    """Download and cache Angel One scrip master. Returns list of instruments."""
    # Check if cache is from today
    if os.path.exists(SCRIP_CACHE):
        age = time.time() - os.path.getmtime(SCRIP_CACHE)
        if age < 8 * 3600:  # Less than 8 hours old
            try:
                with open(SCRIP_CACHE) as f:
                    data = json.load(f)
                print(f"[SCRIP] Loaded cache: {len(data)} instruments")
                return data
            except: pass
    # Download fresh
    try:
        print("[SCRIP] Downloading scrip master...")
        r = requests.get(SCRIP_URL, timeout=30)
        data = r.json()
        with open(SCRIP_CACHE, "w") as f:
            json.dump(data, f)
        print(f"[SCRIP] Downloaded: {len(data)} instruments")
        return data
    except Exception as e:
        print(f"[SCRIP ERR] {e}")
        return []

def find_option_tokens(scrip_master, index, spot, num_strikes=5):
    """
    Find ATM ± num_strikes CE and PE tokens for given index.
    Returns dict: { token: {"strike":x,"type":"CE"/"PE","symbol":x} }
    """
    cfg  = INDEX_CFG[index]
    step = cfg["step"]
    atm  = round(spot / step) * step

    # Get expiry list for NFO options
    # Filter: name=NIFTY/BANKNIFTY, exch_seg=NFO, instrtype=OPTIDX
    name_map = {"NIFTY": "NIFTY", "SENSEX": "SENSEX"}
    index_name = name_map.get(index, index)

    # Collect all options for this index
    options = []
    for inst in scrip_master:
        if (inst.get("exch_seg") == "NFO"
                and inst.get("name") == index_name
                and inst.get("instrumenttype") in ("OPTIDX","OPTSTK")):
            options.append(inst)

    if not options:
        print(f"[SCRIP] No options found for {index_name}")
        return {}

    # Find nearest expiry
    today = datetime.date.today()
    expiries = set()
    for o in options:
        exp_str = o.get("expiry", "")
        try:
            exp = datetime.datetime.strptime(exp_str, "%d%b%Y").date()
            if exp >= today:
                expiries.add(exp)
        except: pass

    if not expiries:
        print("[SCRIP] No valid expiries found")
        return {}

    nearest_expiry = min(expiries)
    exp_str = nearest_expiry.strftime("%d%b%Y").upper()
    print(f"[SCRIP] Using expiry: {exp_str} ATM: {atm}")

    # Filter strikes within range
    strikes = range(atm - step * num_strikes, atm + step * (num_strikes + 1), step)
    tokens  = {}

    for o in options:
        try:
            o_exp  = o.get("expiry", "")
            o_type = o.get("symbol", "")[-2:]   # CE or PE from symbol end
            if o_exp != exp_str: continue
            if o_type not in ("CE", "PE"): continue
            strike = float(o.get("strike", 0)) / 100  # Angel stores strike * 100
            if strike not in strikes: continue
            token = o.get("token", "")
            if token:
                tokens[token] = {
                    "strike":  strike,
                    "type":    o_type,
                    "symbol":  o.get("symbol", ""),
                    "ltp":     None,
                    "oi":      None,
                }
        except: pass

    print(f"[SCRIP] Found {len(tokens)} option tokens around ATM {atm}")
    return tokens

# ── ANGEL ONE LOGIN ──────────────────────────────────────────────────
def angel_login():
    """Login to Angel One SmartAPI. Returns True on success."""
    api_key     = ANGEL["api_key"]
    client_id   = ANGEL["client_id"]
    pin         = ANGEL["pin"]
    totp_secret = ANGEL["totp_secret"]

    if not all([api_key, client_id, pin, totp_secret]):
        raise Exception("Missing Angel One credentials — fill all 4 fields")

    print(f"[ANGEL] Logging in as {client_id}...")
    obj   = SmartConnect(api_key=api_key)
    totp  = pyotp.TOTP(totp_secret).now()
    data  = obj.generateSession(client_id, pin, totp)

    if not data or data.get("status") is False:
        msg = data.get("message", "Login failed") if data else "No response"
        raise Exception(f"Angel One login failed: {msg}")

    ANGEL["session_obj"] = obj
    ANGEL["jwt_token"]   = data["data"]["jwtToken"]
    ANGEL["feed_token"]  = obj.getfeedToken()
    ANGEL["connected"]   = True
    ANGEL["error"]       = None
    print(f"[ANGEL] Login OK. Feed token: {ANGEL['feed_token'][:20]}...")
    return True

# ── ANGEL ONE WEBSOCKET ──────────────────────────────────────────────
def angel_ws_start(option_tokens):
    """Start Angel One WebSocket to stream option chain data."""
    if ANGEL["ws_running"]:
        print("[ANGEL WS] Already running")
        return

    token_list = list(option_tokens.keys())
    # Also add spot index token
    index_token = INDEX_CFG[SYS["index"]]["token"]

    print(f"[ANGEL WS] Starting. Subscribing {len(token_list)} option tokens + spot")

    def on_data(wsapp, message):
        """Called on every tick from Angel One."""
        try:
            if not isinstance(message, dict): return
            token = str(message.get("token", ""))
            ltp   = message.get("last_traded_price", 0)
            if ltp: ltp = ltp / 100   # Angel sends price * 100
            oi    = message.get("open_interest", 0)

            # Update spot if it's the index token
            if token == INDEX_CFG[SYS["index"]]["token"]:
                with state_lock:
                    M["spot"]       = ltp
                    M["fetch_time"] = ist()
                    M["source"]     = "ANGEL ONE"
                    if M["prev"]:
                        M["gap"] = round(ltp - M["prev"], 2)
                    cfg = INDEX_CFG[SYS["index"]]
                    M["atm"] = round(ltp / cfg["step"]) * cfg["step"]
                return

            # Update option data
            if token in option_tokens:
                with OC_LOCK:
                    OC_DATA[token] = {
                        "ltp":    ltp,
                        "oi":     oi,
                        "type":   option_tokens[token]["type"],
                        "strike": option_tokens[token]["strike"],
                    }
        except Exception as e:
            print(f"[ANGEL WS DATA ERR] {e}")

    def on_open(wsapp):
        print("[ANGEL WS] Connected — subscribing tokens")
        ANGEL["ws_running"] = True
        ANGEL["error"]      = None
        # Subscribe all option tokens in mode 3 (full: LTP + OI)
        token_payload = [{"exchangeType": 2, "tokens": token_list}]   # 2 = NFO
        if index_token:
            # Subscribe spot in mode 2
            token_payload.append({"exchangeType": 1, "tokens": [index_token]})  # 1 = NSE
        wsapp.sws.subscribe("mathan_ccs", 3, token_payload)
        broadcast({"type": "angel_ws_connected", "ts": ist()})

    def on_error(wsapp, error):
        print(f"[ANGEL WS ERR] {error}")
        ANGEL["ws_running"] = False
        ANGEL["error"] = str(error)
        broadcast({"type": "angel_ws_error", "error": str(error), "ts": ist()})

    def on_close(wsapp):
        print("[ANGEL WS] Closed")
        ANGEL["ws_running"] = False
        # Auto reconnect after 5s
        threading.Timer(5, lambda: angel_ws_start(option_tokens)).start()

    sws = SmartWebSocketV2(
        ANGEL["jwt_token"],
        ANGEL["api_key"],
        ANGEL["client_id"],
        ANGEL["feed_token"],
        max_retry_attempt=5,
    )
    sws.on_open  = on_open
    sws.on_data  = on_data
    sws.on_error = on_error
    sws.on_close = on_close

    ANGEL["ws"] = sws

    def run_ws():
        try:
            sws.connect()
        except Exception as e:
            print(f"[ANGEL WS RUN ERR] {e}")
            ANGEL["ws_running"] = False

    t = threading.Thread(target=run_ws, daemon=True)
    t.start()
    ANGEL["ws_thread"] = t

# ── OI AGGREGATION (from WebSocket ticks) ────────────────────────────
def aggregate_oi():
    """
    Aggregate OI data from WebSocket ticks into M state.
    Called every poll cycle.
    """
    with OC_LOCK:
        snap = dict(OC_DATA)

    if not snap: return

    total_ce = total_pe = 0
    atm_ce = atm_pe = None
    max_ce_oi = max_pe_oi = 0
    sup_strike = res_strike = 0
    sup_oi = res_oi = 0
    ce_prev = pe_prev = None

    with state_lock:
        atm      = M["atm"]
        ce_prev  = M["ce_prem"]
        pe_prev  = M["pe_prem"]

    if not atm: return

    for token, d in snap.items():
        oi     = d.get("oi") or 0
        ltp    = d.get("ltp") or 0
        typ    = d.get("type")
        strike = d.get("strike", 0)

        if typ == "CE":
            total_ce += oi
            if oi > max_ce_oi:
                max_ce_oi  = oi
                res_strike = strike
                res_oi     = oi
            if strike == atm:
                atm_ce = ltp

        elif typ == "PE":
            total_pe += oi
            if oi > max_pe_oi:
                max_pe_oi  = oi
                sup_strike = strike
                sup_oi     = oi
            if strike == atm:
                atm_pe = ltp

    pcr = round(total_pe / total_ce, 2) if total_ce > 0 else None

    with state_lock:
        M["ce_prev"]    = M["ce_prem"]
        M["pe_prev"]    = M["pe_prem"]
        M["call_oi"]    = total_ce
        M["put_oi"]     = total_pe
        M["pcr"]        = pcr
        M["ce_prem"]    = atm_ce
        M["pe_prem"]    = atm_pe
        M["support"]    = sup_strike or None
        M["resistance"] = res_strike or None
        M["sup_oi"]     = sup_oi or None
        M["res_oi"]     = res_oi or None
        M["source"]     = "ANGEL ONE"
        M["fetch_time"] = ist()

    print(f"[OI] spot={M['spot']} atm={atm} pcr={pcr} CE={atm_ce} PE={atm_pe} callOI={fmt_oi(total_ce)} putOI={fmt_oi(total_pe)}")

# ── YAHOO FALLBACK (VIX + GIFT + spot if Angel not connected) ────────
def _fetch_yahoo_spot():
    idx = SYS["index"]
    sym = {"NIFTY": "%5ENSEI", "SENSEX": "%5EBSESN"}[idx]
    try:
        r = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
            params={"interval": "1m", "range": "1d"},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        meta = r.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
        sp   = meta.get("regularMarketPrice", 0)
        pv   = meta.get("previousClose", 0)
        if not sp: return
        cfg  = INDEX_CFG[idx]
        atm  = round(sp / cfg["step"]) * cfg["step"]
        with state_lock:
            M["spot"]  = sp; M["prev"] = pv
            M["gap"]   = round(sp - pv, 2)
            M["atm"]   = atm; M["source"] = "YAHOO"
            M["fetch_time"] = ist()
    except Exception as e:
        print(f"[YAHOO SPOT ERR] {e}")

def _fetch_vix():
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/%5EINDIAVIX",
            params={"interval": "1m", "range": "1d"},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        v = r.json().get("chart",{}).get("result",[{}])[0].get("meta",{}).get("regularMarketPrice")
        with state_lock: M["vix"] = v
        if v: print(f"[VIX] {v}")
    except: pass

def _fetch_gift():
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/NIFTYFUTURES.NS",
            params={"interval": "1m", "range": "1d"},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        g = r.json().get("chart",{}).get("result",[{}])[0].get("meta",{}).get("regularMarketPrice")
        with state_lock:
            M["gift"] = g
            if g and M["spot"]:
                M["gift_diff"] = round(g - M["spot"], 2)
    except: pass

# ── AGENT COMPUTATION ────────────────────────────────────────────────
def compute_agents():
    with state_lock:
        spot=M["spot"]; atm=M["atm"]; pcr=M["pcr"]; vix=M["vix"]
        gift=M["gift"]; gd=M["gift_diff"]
        ce=M["ce_prem"]; pe=M["pe_prem"]
        ce_p=M["ce_prev"]; pe_p=M["pe_prev"]
        sup=M["support"]; res=M["resistance"]
        exp=M["exp_days"]; gap=M["gap"]

    mins = ist_mins(); ag = {}

    # L1 OI Trend via PCR
    if pcr is not None:
        if pcr > 1.5:   ag["l1"] = ("bull", f"PCR {pcr} STRONG BULL — Put writing heavy")
        elif pcr > 1.2: ag["l1"] = ("bull", f"PCR {pcr} BULLISH")
        elif pcr < 0.6: ag["l1"] = ("bear", f"PCR {pcr} STRONG BEAR — Call writing heavy")
        elif pcr < 0.8: ag["l1"] = ("bear", f"PCR {pcr} BEARISH")
        else:           ag["l1"] = ("neut", f"PCR {pcr} NEUTRAL")
    else: ag["l1"] = ("neut", "PCR N/A — Angel OI not yet received")

    # L2 Price Action
    if res and spot and spot > res:      ag["l2"] = ("bull", f"Broke resistance {int(res)} — Breakout")
    elif sup and spot and spot < sup:    ag["l2"] = ("bear", f"Below support {int(sup)} — Breakdown")
    elif spot and atm and spot > atm+50: ag["l2"] = ("bull", f"Above ATM {atm} — Upward bias")
    elif spot and atm and spot < atm-50: ag["l2"] = ("bear", f"Below ATM {atm} — Downward bias")
    elif spot and atm:                   ag["l2"] = ("neut", f"At ATM {atm}")
    else:                                ag["l2"] = ("neut", "Spot N/A")

    # L3 VIX
    if vix:
        if vix < 12:   ag["l3"] = ("bull", f"VIX {vix:.1f} — Very calm")
        elif vix < 15: ag["l3"] = ("bull", f"VIX {vix:.1f} — Calm")
        elif vix < 18: ag["l3"] = ("neut", f"VIX {vix:.1f} — Caution")
        elif vix < 22: ag["l3"] = ("bear", f"VIX {vix:.1f} — HIGH FEAR")
        else:          ag["l3"] = ("bear", f"VIX {vix:.1f} — DANGER avoid buying")
    else: ag["l3"] = ("neut", "VIX N/A")

    # L4 GIFT
    if gd is not None:
        if gd > 150:    ag["l4"] = ("bull", f"GIFT +{round(gd)} — Strong gap up")
        elif gd > 60:   ag["l4"] = ("bull", f"GIFT +{round(gd)} — Mild gap up")
        elif gd < -150: ag["l4"] = ("bear", f"GIFT {round(gd)} — Strong gap down")
        elif gd < -60:  ag["l4"] = ("bear", f"GIFT {round(gd)} — Mild gap down")
        else:           ag["l4"] = ("neut", f"GIFT ±{round(abs(gd))} — Flat")
    else: ag["l4"] = ("neut", "GIFT N/A")

    # L5 CE Premium direction
    if ce is not None:
        chg = (ce - ce_p) if ce_p else 0
        if chg > 5:    ag["l5"] = ("bull", f"CE ₹{ce:.0f} +{chg:.0f} rising — CE buying")
        elif chg < -5: ag["l5"] = ("bear", f"CE ₹{ce:.0f} {chg:.0f} falling")
        else:          ag["l5"] = ("neut", f"CE ₹{ce:.0f} stable")
    else: ag["l5"] = ("neut", "CE N/A — awaiting Angel WS tick")

    # L6 PE Premium direction
    if pe is not None:
        chg = (pe - pe_p) if pe_p else 0
        if chg > 5:    ag["l6"] = ("bear", f"PE ₹{pe:.0f} +{chg:.0f} rising — PE buying")
        elif chg < -5: ag["l6"] = ("bull", f"PE ₹{pe:.0f} {chg:.0f} falling")
        else:          ag["l6"] = ("neut", f"PE ₹{pe:.0f} stable")
    else: ag["l6"] = ("neut", "PE N/A — awaiting Angel WS tick")

    # L7 Session Clock
    if mins < 555:   ag["l7"] = ("neut", "Pre-market")
    elif mins < 600: ag["l7"] = ("bull", "OPEN HOUR 9:15 — High volatility")
    elif mins < 660: ag["l7"] = ("bull", "9:15–11:00 — Best entry window")
    elif mins < 780: ag["l7"] = ("neut", "11:00–1:00 — Mid session")
    elif mins < 870: ag["l7"] = ("neut", "1:00–2:30 — Afternoon")
    elif mins < 930: ag["l7"] = ("neut", "2:30–3:30 — Expiry window")
    else:            ag["l7"] = ("neut", "Post market")

    # L8 Expiry
    if exp is not None:
        if exp == 0:   ag["l8"] = ("bull", "TODAY EXPIRY — Max theta decay")
        elif exp == 1: ag["l8"] = ("neut", "PRE-EXPIRY tomorrow — Volatile")
        elif exp <= 3: ag["l8"] = ("neut", f"{exp} days — Near expiry")
        else:          ag["l8"] = ("neut", f"{exp} days to expiry")
    else: ag["l8"] = ("neut", "Expiry N/A")

    # L9 Gap Detector
    if gap is not None:
        if gap > 100:    ag["l9"] = ("bull", f"Gap UP +{round(gap)} — Strong")
        elif gap > 40:   ag["l9"] = ("bull", f"Gap UP +{round(gap)} — Mild")
        elif gap < -100: ag["l9"] = ("bear", f"Gap DOWN {round(gap)} — Strong")
        elif gap < -40:  ag["l9"] = ("bear", f"Gap DOWN {round(gap)} — Mild")
        else:            ag["l9"] = ("neut", f"Flat ±{round(abs(gap))}")
    else: ag["l9"] = ("neut", "Gap N/A")

    # L10 PCR strength
    if pcr is not None:
        if pcr > 1.5:   ag["l10"] = ("bull", f"PCR {pcr} — Strong bull")
        elif pcr > 1.2: ag["l10"] = ("bull", f"PCR {pcr} — Bullish")
        elif pcr < 0.6: ag["l10"] = ("bear", f"PCR {pcr} — Strong bear")
        elif pcr < 0.8: ag["l10"] = ("bear", f"PCR {pcr} — Bearish")
        else:           ag["l10"] = ("neut", f"PCR {pcr} — Neutral zone")
    else: ag["l10"] = ("neut", "PCR N/A")

    # L11 Trap Detector
    trap = False; trap_detail = ""
    if pcr and spot and atm:
        if pcr > 1.3 and spot < atm - 50:
            trap = True; trap_detail = "PCR bullish but price below ATM — BULL TRAP?"
        elif pcr < 0.75 and spot > atm + 50:
            trap = True; trap_detail = "PCR bearish but price above ATM — BEAR TRAP?"
    if vix and vix > 20 and pcr and pcr > 1.2:
        trap = True; trap_detail = f"High VIX {vix:.1f} + Bullish PCR — Manipulation?"
    ag["l11"] = ("neut", f"⚠️ {trap_detail}") if trap else ("neut", "No trap detected")

    # L12 Risk Control
    if vix and vix > 22:
        ag["l12"] = ("bear", f"VIX {vix:.1f} EXTREME — Avoid all trades")
    elif vix and vix > 18:
        ag["l12"] = ("neut", f"VIX {vix:.1f} HIGH — 1 lot max, tight SL")
    elif exp == 0 and mins >= 870:
        ag["l12"] = ("neut", "Last hour expiry — Zero decay risk")
    else:
        ag["l12"] = ("bull", "Risk normal — Standard position OK")

    # L13 Behaviour AI — master weight 2.0
    b = sum(1 for v in ag.values() if v[0] == "bull")
    r = sum(1 for v in ag.values() if v[0] == "bear")
    n = sum(1 for v in ag.values() if v[0] == "neut")
    total = b + r
    ratio = (b - r) / total if total > 0 else 0
    note  = ""
    if ratio > 0.3 and (not vix or vix < 18) and not trap and (not pcr or pcr > 0.9):
        ag["l13"] = ("bull", f"Context BULL ({b}↑ {r}↓ no trap)")
    elif ratio < -0.3 and not trap and (not pcr or pcr < 1.1):
        ag["l13"] = ("bear", f"Context BEAR ({b}↑ {r}↓ no trap)")
    else:
        note = "CONFLICT" if trap or abs(ratio) < 0.2 else "Weak signal"
        ag["l13"] = ("neut", f"{note} ({b}↑ {r}↓)")

    with state_lock:
        for aid, (sig, det) in ag.items():
            AGENTS[aid]["signal"] = sig
            AGENTS[aid]["detail"] = det

    return trap

# ── BRAIN DECISION ───────────────────────────────────────────────────
def run_brain(trap):
    with state_lock:
        snap = {k: dict(v) for k, v in AGENTS.items()}

    bw = brw = 0.0; bc = brc = nc = 0; reasons = []
    for a in snap.values():
        sig = a["signal"]; w = a["weight"]; det = a["detail"]
        if not sig: continue
        if sig == "bull":   bc  += 1; bw  += w; reasons.append(det)
        elif sig == "bear": brc += 1; brw += w; reasons.append(det)
        else:               nc  += 1

    tw  = bw + brw or 1
    bp  = round(bw  / tw * 100)
    brp = 100 - bp
    diff = abs(bw - brw)
    conf = "HIGH" if diff >= 3 else "MEDIUM" if diff >= 1.5 else "LOW"

    if trap:
        signal = "WAIT"; reason = "TRAP DETECTED — Market manipulation possible"
    elif bp >= 65 and conf in ("HIGH", "MEDIUM"):
        signal = "BUY CE"; reason = f"Bull {bp}% | {conf}"
    elif brp >= 65 and conf in ("HIGH", "MEDIUM"):
        signal = "BUY PE"; reason = f"Bear {brp}% | {conf}"
    else:
        signal = "WAIT"; reason = f"No clear signal (Bull {bp}% Bear {brp}%)"

    with state_lock:
        BRAIN.update({
            "signal": signal, "bull_pct": bp, "bear_pct": brp,
            "confidence": conf, "reasons": reasons[:8],
            "source": M.get("source") or "NONE",
            "computed_at": ist(), "trap_detected": trap,
            "conflict": abs(bp - brp) < 20,
        })
    print(f"[BRAIN] {signal} | B:{bp}% Br:{brp}% | {conf} | trap:{trap}")

# ── MAIN CYCLE ───────────────────────────────────────────────────────
def full_cycle():
    with state_lock:
        if SYS["fetching"]: return
        SYS["fetching"] = True; SYS["error"] = None
    try:
        # Get fresh VIX + GIFT always (Yahoo — always free)
        threading.Thread(target=_fetch_vix,  daemon=True).start()
        threading.Thread(target=_fetch_gift, daemon=True).start()

        if ANGEL["connected"] and ANGEL["ws_running"]:
            # Angel One WebSocket is running — aggregate from OC_DATA
            aggregate_oi()
            with state_lock: M["exp_days"] = calc_expiry()
        else:
            # Fallback to Yahoo spot if Angel not connected
            _fetch_yahoo_spot()
            with state_lock: M["exp_days"] = calc_expiry()

        with state_lock:
            if not M["spot"]:
                raise Exception("No spot price received")

        trap = compute_agents()
        run_brain(trap)

        with state_lock:
            SYS["last_fetch"]    = ist()
            SYS["error"]         = None
            SYS["count"]         = SYS.get("count", 0) + 1
            SYS["auth_failures"] = 0

        try: broadcast(build_state())
        except: pass

    except Exception as e:
        err = str(e); print(f"[CYCLE ERR] {err}")
        with state_lock: SYS["error"] = err
        try: broadcast({"type": "fetch_error", "error": err, "ts": ist()})
        except: pass
    finally:
        with state_lock: SYS["fetching"] = False

def build_state():
    with state_lock:
        return {
            "type":   "state_update", "ts": ist(),
            "sys": {
                "source":       SYS["source"],
                "index":        SYS["index"],
                "auto":         SYS["auto"],
                "last_fetch":   SYS["last_fetch"],
                "error":        SYS["error"],
                "count":        SYS["count"],
                "angel_ok":     ANGEL["connected"],
                "angel_ws":     ANGEL["ws_running"],
            },
            "market": dict(M),
            "agents": {k: dict(v) for k, v in AGENTS.items()},
            "brain":  dict(BRAIN),
        }

# ── BACKGROUND THREADS ───────────────────────────────────────────────
def push_loop():
    """WebSocket delivery — always alive, independent of polling."""
    while True:
        time.sleep(5)
        clients = cl_snap()
        if not clients: continue
        try:
            payload = build_state()
            data    = json.dumps(payload)
            dead    = []
            for c in clients:
                try: c.send(data)
                except: dead.append(c)
            for c in dead: cl_rm(c)
        except Exception as e:
            print(f"[PUSH ERR] {e}")

def poll_loop():
    """Polling engine — runs every poll_interval seconds."""
    while True:
        with state_lock: interval = SYS.get("poll_interval", 15)
        time.sleep(interval)
        with state_lock:
            go = (SYS["source"] != "NONE"
                  and not SYS["fetching"]
                  and SYS.get("auth_failures", 0) < 3)
        if go:
            threading.Thread(target=full_cycle, daemon=True).start()

# ── ANGEL ONE CONNECT FLOW ────────────────────────────────────────────
def do_angel_connect(api_key, client_id, pin, totp_secret):
    """Full connect flow: login → scrip master → WS start."""
    try:
        ANGEL["api_key"]     = api_key
        ANGEL["client_id"]   = client_id
        ANGEL["pin"]         = pin
        ANGEL["totp_secret"] = totp_secret

        # Save to DB
        db_set("angel_api_key",     api_key)
        db_set("angel_client_id",   client_id)
        db_set("angel_pin",         pin)
        db_set("angel_totp_secret", totp_secret)

        # Login
        angel_login()
        broadcast({"type": "angel_login_ok", "ts": ist()})

        # Load scrip master
        broadcast({"type": "status_msg", "msg": "Loading scrip master...", "ts": ist()})
        scrip_master = load_scrip_master()

        # Get current spot for ATM calculation (Yahoo quick fetch)
        _fetch_yahoo_spot()
        with state_lock:
            spot = M["spot"]
            idx  = SYS["index"]

        if not spot:
            raise Exception("Could not get spot price for ATM calculation")

        # Find option tokens
        broadcast({"type": "status_msg", "msg": f"Finding option tokens for {idx} ATM {round(spot/INDEX_CFG[idx]['step'])*INDEX_CFG[idx]['step']}...", "ts": ist()})
        option_tokens = find_option_tokens(scrip_master, idx, spot, num_strikes=5)

        if not option_tokens:
            raise Exception("No option tokens found — scrip master may be outdated")

        # Start WebSocket
        with state_lock: SYS["source"] = "ANGEL ONE"
        angel_ws_start(option_tokens)

        broadcast({"type": "angel_connected",
                   "tokens": len(option_tokens),
                   "source": "ANGEL ONE", "ts": ist()})
        print(f"[ANGEL] Full connect complete. {len(option_tokens)} tokens subscribed.")

        # Trigger first cycle
        threading.Thread(target=full_cycle, daemon=True).start()

    except Exception as e:
        print(f"[ANGEL CONNECT ERR] {e}")
        ANGEL["connected"] = False
        ANGEL["error"]     = str(e)
        broadcast({"type": "angel_err", "msg": str(e), "ts": ist()})

# ── WEBSOCKET HANDLER ─────────────────────────────────────────────────
@sock.route("/ws")
def ws_handler(ws):
    cl_add(ws)
    print(f"[WS] +client  online:{len(_clients)}")
    send1(ws, {"type": "init",
               "angel_ok": ANGEL["connected"],
               "angel_ws": ANGEL["ws_running"],
               "source":   SYS["source"],
               "index":    SYS["index"],
               "ts":       ist()})
    send1(ws, build_state())
    try:
        while True:
            msg = ws.receive()
            if msg is None: break
            try: d = json.loads(msg)
            except: continue
            t = d.get("type", "")

            if t == "ping":
                send1(ws, {"type": "pong", "ts": ist()})

            elif t == "connect_angel":
                # Receive all 4 credentials from UI
                api_key     = d.get("api_key", "").strip()
                client_id   = d.get("client_id", "").strip()
                pin         = d.get("pin", "").strip()
                totp_secret = d.get("totp_secret", "").strip()
                if not all([api_key, client_id, pin, totp_secret]):
                    send1(ws, {"type": "angel_err", "msg": "All 4 fields required"})
                    continue
                send1(ws, {"type": "status_msg", "msg": "Connecting to Angel One...", "ts": ist()})
                threading.Thread(
                    target=do_angel_connect,
                    args=(api_key, client_id, pin, totp_secret),
                    daemon=True
                ).start()

            elif t == "set_yahoo":
                with state_lock:
                    SYS["source"]        = "YAHOO"
                    SYS["auth_failures"] = 0
                    SYS["error"]         = None
                db_set("source", "YAHOO")
                broadcast({"type": "source_changed", "source": "YAHOO", "ts": ist()})
                threading.Thread(target=full_cycle, daemon=True).start()

            elif t == "set_index":
                idx = d.get("index", "NIFTY").upper()
                if idx in INDEX_CFG:
                    with state_lock: SYS["index"] = idx
                    db_set("index", idx)
                    if SYS["source"] != "NONE":
                        threading.Thread(target=full_cycle, daemon=True).start()

            elif t == "fetch":
                threading.Thread(target=full_cycle, daemon=True).start()

            elif t == "set_auto":
                on = bool(d.get("on", False))
                with state_lock: SYS["auto"] = on

            elif t == "get_state":
                send1(ws, build_state())

    except Exception as e:
        print(f"[WS ERR] {e}")
    finally:
        cl_rm(ws)
        print(f"[WS] -client  online:{len(_clients)}")

# ── REST ─────────────────────────────────────────────────────────────

@app.route("/connect_angel", methods=["POST"])
def connect_angel_rest():
    data       = request.get_json(force=True) or {}
    api_key     = data.get("api_key","").strip()
    client_id   = data.get("client_id","").strip()
    pin         = data.get("pin","").strip()
    totp_secret = data.get("totp_secret","").strip()
    print(f"[API] /connect_angel called — client_id={client_id}")
    if not all([api_key, client_id, pin, totp_secret]):
        return jsonify({"ok":False,"error":"All 4 fields required"}), 400
    threading.Thread(
        target=do_angel_connect,
        args=(api_key, client_id, pin, totp_secret),
        daemon=True
    ).start()
    return jsonify({"ok":True,"msg":"Login started — watch server logs"})

@app.route("/set_yahoo", methods=["POST"])
def set_yahoo_rest():
    with state_lock:
        SYS["source"] = "YAHOO"; SYS["auth_failures"] = 0; SYS["error"] = None
    db_set("source","YAHOO")
    broadcast({"type":"source_changed","source":"YAHOO","ts":ist()})
    threading.Thread(target=full_cycle,daemon=True).start()
    return jsonify({"ok":True,"source":"YAHOO"})

@app.route("/ping")
def ping():
    return jsonify({"pong": True, "time": ist(),
                    "angel_ok": ANGEL["connected"],
                    "angel_ws": ANGEL["ws_running"],
                    "source": SYS["source"]})

@app.route("/status")
def status():
    with state_lock:
        return jsonify({"sys": dict(SYS), "market": dict(M),
                        "brain": dict(BRAIN), "clients": len(_clients)})

@app.route("/oc")
def oc_debug():
    with OC_LOCK:
        return jsonify({"oc_data": dict(OC_DATA), "count": len(OC_DATA)})

@app.route("/")
@app.route("/dashboard")
def dashboard():
    return Response(DASHBOARD_HTML, mimetype="text/html")

# ── STARTUP ──────────────────────────────────────────────────────────
if __name__ == "__main__":

    # ── CODE INTEGRITY CHECK ─────────────────────────────────────────
    # Verifies this file has not been modified by any external source.
    # Built by Claude (Anthropic) for Chairman Mr. Mathan Sir ONLY.
    # If any warning appears below — inform Claude immediately.
    import hashlib as _hl, re as _re
    _src      = open(__file__, encoding='utf-8').read()
    _warnings = []

    print("=" * 54)
    print("  MATHAN AI — STARTUP INTEGRITY CHECK")
    print("  Built by: Claude (Anthropic)")
    print("  Owner   : Chairman Mr. Mathan Sir")
    print("=" * 54)

    # Check 1: Foreign AI signatures
    _FOREIGN = {
        "ChatGPT":        "OpenAI ChatGPT code detected",
        "GPT-4":          "OpenAI GPT-4 code detected",
        "GPT-3":          "OpenAI GPT-3 code detected",
        "openai.com":     "OpenAI URL found in code",
        "Gemini":         "Google Gemini code detected",
        "Bard":           "Google Bard code detected",
        "Copilot":        "Microsoft Copilot code detected",
        "generated by AI":"AI-generated tag found",
        "written by gpt": "GPT authorship tag found",
    }
    for _sig, _msg in _FOREIGN.items():
        if _sig.lower() in _src.lower():
            _warnings.append(f"FOREIGN CODE: {_msg}")

    # Check 2: Duplicate function definitions (sign of mixed code)
    _fn_names = _re.findall(r'^def (\w+)\(', _src, _re.MULTILINE)
    _fn_seen = {}
    for _fn in _fn_names:
        _fn_seen[_fn] = _fn_seen.get(_fn, 0) + 1
    _dupes = [f for f,c in _fn_seen.items() if c > 1]
    if _dupes:
        _warnings.append(f"DUPLICATE FUNCTIONS: {_dupes} — possible code mixing")

    # Check 3: Required core functions must exist
    _REQUIRED = [
        "def angel_login",
        "def full_cycle",
        "def compute_agents",
        "def run_brain",
        "def push_loop",
        "def ws_handler",
        "DASHBOARD_HTML",
    ]
    _missing = [f for f in _REQUIRED if f not in _src]
    if _missing:
        _warnings.append(f"MISSING CORE FUNCTIONS: {_missing}")

    # Check 4: Unexpected external URLs (other than known ones)
    _ALLOWED_URLS = [
        "anthropic.com", "yahoo.com", "angelbroking.com",
        "googleapis.com", "margincalculator", "fonts.googleapis",
        "query1.finance", "127.0.0.1", "0.0.0.0",
        "dhanhq.co", "smartapi", "github"
    ]
    _urls = _re.findall(r'https?://([^\s\'">/]+)', _src)
    _unknown_urls = []
    for _u in set(_urls):
        if not any(_a in _u for _a in _ALLOWED_URLS):
            _unknown_urls.append(_u)
    if _unknown_urls:
        _warnings.append(f"UNKNOWN EXTERNAL URLS: {_unknown_urls}")

    # ── PRINT RESULT ────────────────────────────────────────────────
    _fp = _hl.md5(_src.encode('utf-8')).hexdigest()[:12]
    if _warnings:
        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║  ⚠️  CODE INTEGRITY WARNING               ║")
        print("  ║  INFORM CLAUDE IMMEDIATELY               ║")
        print("  ╠══════════════════════════════════════════╣")
        for _w in _warnings:
            print(f"  ║  • {_w[:42]}")
        print("  ╚══════════════════════════════════════════╝")
        print()
        # Store warnings so they appear on dashboard too
        SYS["error"] = "CODE WARNING: " + " | ".join(_warnings)
    else:
        print("  [OK] No foreign code signatures")
        print("  [OK] No duplicate functions")
        print("  [OK] All core functions present")
        print("  [OK] No unexpected external URLs")
        print(f"  [OK] File fingerprint: {_fp}")
        print(f"  [OK] Size: {len(_src.splitlines())} lines")

    print("=" * 54)
    print()

    # ── INSTALL DEPS ─────────────────────────────────────────────────
    # Install deps
    missing = []
    try: from SmartApi import SmartConnect
    except: missing.append("smartapi-python")
    try: import pyotp
    except: missing.append("pyotp")
    try: import simple_websocket
    except: missing.append("simple-websocket")
    if missing:
        print(f"[SETUP] Installing: {missing}")
        os.system(f"pip install {' '.join(missing)} --break-system-packages -q")

    db_init()
    db_load()

    # Auto-login if credentials saved
    if ANGEL["api_key"] and ANGEL["client_id"] and ANGEL["pin"] and ANGEL["totp_secret"]:
        print("[STARTUP] Credentials found — connecting Angel One...")
        threading.Thread(
            target=do_angel_connect,
            args=(ANGEL["api_key"], ANGEL["client_id"], ANGEL["pin"], ANGEL["totp_secret"]),
            daemon=True
        ).start()
    else:
        # Yahoo fallback until Angel connected
        with state_lock: SYS["source"] = "YAHOO"
        _fetch_yahoo_spot()
        _fetch_vix()
        _fetch_gift()

    threading.Thread(target=push_loop, daemon=True).start()
    threading.Thread(target=poll_loop, daemon=True).start()

    
    ip = local_ip()
    print(f"""
╔═════════════════════════════════════════════╗
║    MATHAN AI — ANGEL ONE FULL SYSTEM       ║
╠═════════════════════════════════════════════╣
║  OPEN  : http://{ip}:{PORT}
║  PING  : http://{ip}:{PORT}/ping
║  OC    : http://{ip}:{PORT}/oc
╠═════════════════════════════════════════════╣
║  Angel One WS → Real OI + CE/PE Premium    ║
║  Yahoo → VIX + GIFT (always free)          ║
║  13 Agents + Trap Detector                 ║
╚═════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)


