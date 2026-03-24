from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "MATHAN AI HEMAN - LIVE!"

@app.route("/ping")
def ping():
    return '{"status":"OK"}'
