import sqlite3
from datetime import datetime

DB_NAME = "imsg_data.db"


# ----------------------------
# Initialize Database
# ----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT,
            confidence REAL,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


# ----------------------------
# Save Detection
# ----------------------------
def save_detection(label, confidence):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO detections (label, confidence, timestamp)
        VALUES (?, ?, ?)
    """, (label, confidence, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()


# ----------------------------
# Get All Detections
# ----------------------------
def get_all_detections():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, label, confidence, timestamp
        FROM detections
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    detections = []
    for row in rows:
        detections.append({
            "id": row[0],
            "label": row[1],
            "confidence": row[2],
            "timestamp": row[3]
        })

    return detections


# ----------------------------
# Get Detections By Date
# ----------------------------
def get_detections_by_date(start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, label, confidence, timestamp
        FROM detections
        WHERE date(timestamp) BETWEEN date(?) AND date(?)
        ORDER BY id DESC
    """, (start_date, end_date))

    rows = cursor.fetchall()
    conn.close()

    detections = []
    for row in rows:
        detections.append({
            "id": row[0],
            "label": row[1],
            "confidence": row[2],
            "timestamp": row[3]
        })

    return detections