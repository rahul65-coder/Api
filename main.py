import os
import json
import time
import requests
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Load Firebase Key from Environment Variable
firebase_key_json = os.environ.get("FIREBASE_KEY")
firebase_key_dict = json.loads(firebase_key_json)

# 🧠 Firebase Config
cred = credentials.Certificate(firebase_key_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://web-admin-e297c-default-rtdb.asia-southeast1.firebasedatabase.app'
})

ref = db.reference("satta_results")

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

def get_size_label(number):
    return "SMALL" if number <= 4 else "BIG"

def fetch_and_save():
    try:
        response = requests.get(API_URL, headers=HEADERS)
        data = response.json()
        items = data["data"]["list"][:10]

        for item in items:
            issue = str(item["issueNumber"])
            number = int(item["number"])
            size = get_size_label(number)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if ref.child(issue).get() is None:
                ref.child(issue).set({
                    "result_number": number,
                    "type": size,
                    "timestamp": timestamp
                })
                print(f"✅ Saved: {issue} → {number} ({size}) @ {timestamp}")
            else:
                print(f"⚠️ Skipped (exists): {issue}")

    except Exception as e:
        print("❌ Fetch error:", e)

def wait_until_next_minute():
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    time.sleep((next_minute - now).total_seconds())

def run_loop():
    while True:
        fetch_and_save()
        wait_until_next_minute()

if __name__ == "__main__":
    run_loop()