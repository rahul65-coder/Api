from flask import Flask
import requests
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
import os

app = Flask(__name__)

# ✅ Firebase Setup
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://web-admin-e297c-default-rtdb.asia-southeast1.firebasedatabase.app'
    })
    ref = db.reference("satta")
    print("✅ Firebase initialized.")
except Exception as e:
    print("❌ Firebase initialization error:", e)

# 🧠 API URL
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

def get_size_label(number):
    return "SMALL" if number <= 4 else "BIG"

def fetch_and_save():
    logs = []
    try:
        response = requests.get(API_URL, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        })

        logs.append(f"🌐 API status: {response.status_code}")
        if response.status_code != 200:
            logs.append("❌ Invalid response from API")
            return "\n".join(logs)

        data = response.json()
        items = data.get("data", {}).get("list", [])[:10]
        logs.append(f"📦 Total Items Fetched: {len(items)}")

        for item in items:
            issue = str(item.get("issueNumber", "")).replace("-", "").strip()
            number = int(item.get("number", -1))
            if number == -1:
                logs.append(f"⚠️ Invalid number in item: {item}")
                continue

            size = get_size_label(number)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if ref.child(issue).get() is None:
                ref.child(issue).set({
                    "result_number": number,
                    "type": size,
                    "timestamp": timestamp
                })
                logs.append(f"✅ Saved: {issue} → {number} ({size}) @ {timestamp}")
            else:
                logs.append(f"⚠️ Skipped (already exists): {issue}")

    except Exception as e:
        logs.append(f"❌ Error: {str(e)}")

    return "\n".join(logs)


@app.route('/')
def index():
    return '<h1>Satta Running</h1><p>Use /run to fetch results.</p>'

@app.route('/run')
def run_fetcher():
    print("🚀 /run endpoint hit!")
    output = fetch_and_save()
    print("🧾 Log Output:\n", output)
    return f"<pre>{output}</pre>"


if __name__ == "__main__":
    app.run(debug=True)
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
