import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Load Firebase credentials from environment variable
firebase_key_json = os.environ.get("FIREBASE_KEY")
firebase_key_dict = json.loads(firebase_key_json)

# 🔌 Initialize Firebase
cred = credentials.Certificate(firebase_key_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://web-admin-e297c-default-rtdb.asia-southeast1.firebasedatabase.app'
})

ref = db.reference("satta_results")

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

# 🚀 Flask app to keep service alive on Render
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Satta fetcher is running!", 200

@app.route("/test")
def test():
    fetch_and_save()
    return "✅ Manual fetch triggered!", 200

def get_size_label(number):
    return "SMALL" if number <= 4 else "BIG"

def fetch_and_save():
    print("\n🚀 Running fetch_and_save...")

    try:
        response = requests.get(API_URL, headers=HEADERS)
        print(f"🌐 API Status Code: {response.status_code}")

        data = response.json()
        items = data["data"]["list"][:10]
        print(f"📦 Total items fetched: {len(items)}")

        for item in items:
            issue = str(item.get("issueNumber"))
            number = int(item.get("number", -1))
            size = get_size_label(number)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"🔍 Checking issue: {issue}, number: {number}")

            if ref.child(issue).get() is None:
                ref.child(issue).set({
                    "result_number": number,
                    "type": size,
                    "timestamp": timestamp
                })
                print(f"✅ Saved: {issue} → {number} ({size}) @ {timestamp}")
            else:
                print(f"⚠️ Skipped (already exists): {issue}")

    except Exception as e:
        print("❌ ERROR in fetch_and_save:", e)

def wait_until_next_minute():
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    sleep_time = (next_minute - now).total_seconds()
    print(f"⏳ Sleeping for {sleep_time:.2f} seconds...\n")
    time.sleep(sleep_time)

def background_loop():
    while True:
        fetch_and_save()
        wait_until_next_minute()

if __name__ == "__main__":
    # Start background thread
    t = threading.Thread(target=background_loop)
    t.daemon = True
    t.start()

    # Start Flask server
    port = int(os.environ.get("PORT", 10000))
    print(f"🌍 Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port)
