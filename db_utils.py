# db_utils.py
import sqlite3
import hashlib
import time

DB_NAME = "history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            text_hash TEXT,
            prediction TEXT,
            confidence REAL,
            n_words INTEGER
        )
    """)
    conn.commit()
    conn.close()

def log_result(text: str, prediction: str, confidence: float, n_words: int):
    """Store a detection result in the database"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    cur.execute(
        "INSERT INTO history (timestamp, text_hash, prediction, confidence, n_words) VALUES (?, ?, ?, ?, ?)",
        (time.time(), text_hash, prediction, confidence, n_words)
    )
    conn.commit()
    conn.close()

def fetch_all():
    """Fetch all logged results"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, text_hash, prediction, confidence, n_words FROM history ORDER BY timestamp DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
