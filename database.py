import sqlite3
from datetime import datetime
from config import DATA_DIR, DATABASE_PATH

def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            started_at TEXT NOT NULL,
            duration_seconds REAL,
            size_bytes INTEGER,
            cpu_temperature_c REAL
        );
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER NOT NULL,
            species TEXT NOT NULL,
            confidence REAL,
            start_seconds REAL,
            end_seconds REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(recording_id) REFERENCES recordings(id)
        );
        """)

def save_recording(file_path, processed_info, environment):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO recordings
            (file_path, started_at, duration_seconds, size_bytes, cpu_temperature_c)
            VALUES (?, ?, ?, ?, ?)""",
            (
                str(file_path),
                environment["timestamp"],
                processed_info["duration_seconds"],
                processed_info["size_bytes"],
                environment["cpu_temperature_c"],
            ),
        )
        return cur.lastrowid

def save_detection(recording_id, species, confidence,
                   start_seconds=None, end_seconds=None):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO detections
            (recording_id, species, confidence, start_seconds,
             end_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                recording_id, species, confidence,
                start_seconds, end_seconds,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

def recent_detections(limit=50):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT detections.*, recordings.file_path
            FROM detections
            JOIN recordings ON detections.recording_id = recordings.id
            ORDER BY detections.created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

def recent_recordings(limit=20):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM recordings ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DATABASE_PATH}")
