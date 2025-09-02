import sqlite3
import time
import requests
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
DATABASE = 'performance_data.db'  # SQLite database file

# --- Database Initialization ---
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS response_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                api_name TEXT NOT NULL,
                response_time REAL NOT NULL,
                status_code INTEGER NOT NULL,
                error_message TEXT
            )
        ''')
        conn.commit()
    print("Database initialized.")

# --- API Monitoring Function ---
def monitor_api(api_name, url):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')  # Line 29 — indented
    response_time = 0.0
    status_code = -1
    error_message = None

    try:
        start_time = time.monotonic()
        response = requests.get(url, timeout=5)
        end_time = time.monotonic()
        response_time = (end_time - start_time) * 1000  # ms
        status_code = response.status_code
        print(f"[{api_name}] response time: {response_time:.2f}ms, Status: {status_code}")

    except requests.exceptions.Timeout:
        response_time = 5000.0  # assume full timeout duration
        error_message = "Timeout"
        print(f"[{api_name}] Timeout after {response_time:.2f}ms")

    except requests.exceptions.ConnectionError:
        response_time = 0.0
        error_message = "Connection Error"
        print(f"[{api_name}] Connection Error")

    except Exception as e:
        response_time = 0.0
        error_message = str(e)
        print(f"[{api_name}] Unexpected error: {error_message}")

    # Always log the result
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO response_times 
               (timestamp, api_name, response_time, status_code, error_message) 
               VALUES (?, ?, ?, ?, ?)''',
            (timestamp, api_name, response_time, status_code, error_message)
        )
        conn.commit()

# --- Scheduler Setup ---
scheduler = BackgroundScheduler()

MONITORED_APIS = {
    "Google": "https://www.google.com",
    "GitHub": "https://api.github.com",
    "NonExistentAPI": "http://this-api-does-not-exist.com"
}

def start_monitoring_jobs():
    for api_name, url in MONITORED_APIS.items():
        scheduler.add_job(
            monitor_api,
            'interval',
            seconds=10,
            args=[api_name, url],
            id=f'monitor_{api_name}',
            replace_existing=True
        )
    scheduler.start()
    print("API monitoring jobs started.")

# --- Flask Routes ---
@app.route('/')
def index():
    return "API Performance Monitor is running. Access /metrics to see collected data."

@app.route('/metrics')
def get_metrics():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM response_times ORDER BY timestamp DESC LIMIT 100")
    metrics = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(metrics)

# --- Application Startup ---
if __name__ == '__main__':
    init_db()
    start_monitoring_jobs()
    app.run(debug=True, use_reloader=False)