import sqlite3
from datetime import datetime
from config import DATA_DIR, DATABASE_PATH


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            started_at TEXT NOT NULL,
            duration_seconds REAL,
            size_bytes INTEGER,
            cpu_temperature_c REAL,
            audio_rms REAL,
            audio_peak INTEGER,
            sound_level TEXT
        );

        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER NOT NULL,
            species TEXT NOT NULL,
            confidence REAL,
            start_seconds REAL,
            end_seconds REAL,
            created_at TEXT NOT NULL,
            model_name TEXT NOT NULL DEFAULT 'BirdNET',
            category TEXT NOT NULL DEFAULT 'bird',
            scientific_name TEXT,
            FOREIGN KEY(recording_id) REFERENCES recordings(id)
        );
        """)
        # Safe additive migrations preserve an existing database.
        recording_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(recordings)")
        }
        for name, kind in {
            "audio_rms": "REAL",
            "audio_peak": "INTEGER",
            "sound_level": "TEXT",
        }.items():
            if name not in recording_columns:
                conn.execute(f"ALTER TABLE recordings ADD COLUMN {name} {kind}")

        detection_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(detections)")
        }
        for name, kind in {
            "model_name": "TEXT NOT NULL DEFAULT 'BirdNET'",
            "category": "TEXT NOT NULL DEFAULT 'bird'",
            "scientific_name": "TEXT",
        }.items():
            if name not in detection_columns:
                conn.execute(f"ALTER TABLE detections ADD COLUMN {name} {kind}")


def save_recording(file_path, processed_info, environment):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO recordings (
                file_path, started_at, duration_seconds, size_bytes,
                cpu_temperature_c, audio_rms, audio_peak, sound_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(file_path), environment["timestamp"],
            processed_info["duration_seconds"], processed_info["size_bytes"],
            environment.get("cpu_temperature_c"), environment.get("audio_rms"),
            environment.get("audio_peak"), environment.get("sound_level", "unknown"),
        ))
        return cursor.lastrowid


def save_detection(recording_id, detection):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO detections (
                recording_id, species, confidence, start_seconds, end_seconds,
                created_at, model_name, category, scientific_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recording_id, detection.get("label") or detection.get("species") or "Unknown",
            detection.get("confidence"), detection.get("start_seconds"),
            detection.get("end_seconds"),
            datetime.now().isoformat(timespec="seconds"),
            detection.get("model_name", "unknown"),
            detection.get("category", "unknown"),
            detection.get("scientific_name"),
        ))


def recent_detections(limit=100):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT detections.*, recordings.file_path
            FROM detections
            JOIN recordings ON detections.recording_id = recordings.id
            ORDER BY detections.created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]


def recent_recordings(limit=30):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM recordings ORDER BY started_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DATABASE_PATH}")
