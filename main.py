import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, Response
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Firebase credentials from ENV
firebase_key_json = os.environ.get("FIREBASE_KEY")
firebase_key_dict = json.loads(firebase_key_json)

# 🔌 Firebase init
cred = credentials.Certificate(firebase_key_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://web-admin-e297c-default-rtdb.asia-southeast1.firebasedatabase.app'
})

ref = db.reference("satta_results")

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Satta fetcher running!"

@app.route("/test")
def test():
    log_lines = []  # Collect output for browser

    def log(msg):
        print(msg)           # Print in console (Render logs)
        log_lines.append(msg)  # Save for browser response

    log("\n🚀 /test route triggered...")

    try:
        response = requests.get(API_URL, headers=HEADERS)
        log(f"🌐 API Status Code: {response.status_code}")

        data = response.json()
        items = data["data"]["list"][:10]
        log(f"📦 Items fetched: {len(items)}")

        for item in items:
            issue = str(item.get("issueNumber"))
            number = int(item.get("number", -1))
            size = get_size_label(number)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            log(f"🔍 Issue: {issue}, Number: {number}, Size: {size}")

            if ref.child(issue).get() is None:
                ref.child(issue).set({
                    "result_number": number,
                    "type": size,
                    "timestamp": timestamp
                })
                log(f"✅ Saved: {issue} → {number} ({size}) @ {timestamp}")
            else:
                log(f"⚠️ Skipped (exists): {issue}")

    except Exception as e:
        error_msg = f"❌ ERROR: {str(e)}"
        log(error_msg)

    return Response("<br>".join(log_lines), mimetype='text/html')

def get_size_label(number):
    return "SMALL" if number <= 4 else "BIG"

def wait_until_next_minute():
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    time.sleep((next_minute - now).total_seconds())

def background_loop():
    while True:
        fetch_and_save()
        wait_until_next_minute()

def fetch_and_save():
    try:
        response = requests.get(API_URL, headers=HEADERS)
        data = response.json()
        items = data["data"]["list"][:10]

        for item in items:
            issue = str(item.get("issueNumber"))
            number = int(item.get("number", -1))
            size = get_size_label(number)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if ref.child(issue).get() is None:
                ref.child(issue).set({
                    "result_number": number,
                    "type": size,
                    "timestamp": timestamp
                })
                print(f"✅ [Auto] Saved: {issue} → {number} ({size}) @ {timestamp}")
            else:
                print(f"⚠️ [Auto] Skipped: {issue} already exists.")

    except Exception as e:
        print("❌ [Auto] ERROR:", e)

if __name__ == "__main__":
    t = threading.Thread(target=background_loop)
    t.daemon = True
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
