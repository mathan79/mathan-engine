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
    <div class="pcr-sig" id="pcrSig" style="color:var(--gold)">Awaiting Angel