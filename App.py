"""
MATHAN AI — ANGEL ONE FULL INTEGRATION WITH CP BUTTON
======================================================
"""
import os, json, time, threading, datetime, socket
import pyotp
from SmartApi import SmartConnect
from flask import Flask, Response, jsonify, request

# --- DASHBOARD HTML ---
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Mathan AI - Angel One Brain</title>
    <style>
        :root{--bg:#070b0f;--bg2:#0d1419;--accent:#00ffcc;--text:#e0e6ed;}
        body{background:var(--bg);color:var(--text);font-family:sans-serif;margin:0;padding:20px;}
        .container{max-width:800px;margin:auto;background:var(--bg2);padding:20px;border-radius:12px;}
        input{background:#1a242d;border:1px solid #334155;color:white;padding:12px;border-radius:6px;width:70%;}
        button{background:var(--accent);color:black;border:none;padding:12px 20px;border-radius:6px;cursor:pointer;font-weight:bold;}
        .cp-btn{background:#4b5563;color:white;margin-left:5px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>Mathan AI Dashboard</h2>
        <div style="margin-bottom:20px;">
            <input type="text" id="dhan_token" placeholder="Paste Token Here">
            <button class="cp-btn" onclick="pasteToken()">CP</button>
        </div>
        <button onclick="connectDhan()">CONNECT DHAN</button>
    </div>

    <script>
        async function pasteToken() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('dhan_token').value = text;
            } catch (err) {
                alert("கிளிப்போர்டு அணுகல் மறுக்கப்பட்டது!");
            }
        }
        function connectDhan() {
            alert("Dhan உடன் இணைக்கப்படுகிறது...");
        }
    </script>
</body>
</html>"""

app = Flask(__name__)

@app.route('/')
def index():
    return DASHBOARD_HTML

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
