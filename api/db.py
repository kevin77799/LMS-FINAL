import sqlite3
import hashlib
from datetime import datetime
from typing import Optional

from .core.config import DB_PATH


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()


    c.execute(
        '''CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               username TEXT UNIQUE,
               password TEXT,
               course_id TEXT,
               education_level TEXT,
               admin_id INTEGER,
               FOREIGN KEY(admin_id) REFERENCES admin_users(id))'''
    )
    
    # Simple migration for existing tables
    try:
        c.execute("ALTER TABLE users ADD COLUMN admin_id INTEGER REFERENCES admin_users(id)")
    except Exception:
        pass

    # Admin Table
    c.execute(
        '''CREATE TABLE IF NOT EXISTS admin_users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               username TEXT UNIQUE,
               email TEXT,
               password TEXT,
               admin_code TEXT UNIQUE)'''
    )
    
    try:
        c.execute("ALTER TABLE admin_users ADD COLUMN admin_code TEXT UNIQUE")
    except Exception:
        pass

    try:
        c.execute("ALTER TABLE admin_users ADD COLUMN email TEXT")
    except Exception:
        pass

    # OTP Table for Setup
    c.execute(
        '''CREATE TABLE IF NOT EXISTS admin_otp (
               code TEXT PRIMARY KEY,
               created_at TEXT)'''
    )

    c.execute(
        '''CREATE TABLE IF NOT EXISTS file_groups (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER,
               group_name TEXT,
               created_at TEXT,
               FOREIGN KEY(user_id) REFERENCES users(id))'''
    )

    c.execute(
        '''CREATE TABLE IF NOT EXISTS files (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               group_id INTEGER,
               file_name TEXT,
               file_type TEXT,
               file_content BLOB,
               uploaded_at TEXT,
               FOREIGN KEY(group_id) REFERENCES file_groups(id))'''
    )

    c.execute(
        '''CREATE TABLE IF NOT EXISTS syllabus (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               course_id TEXT,
               syllabus_content TEXT,
               saved_at TEXT)'''
    )

    c.execute(
        '''CREATE TABLE IF NOT EXISTS syllabus_for_students (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               group_id TEXT,
               syllabus_content TEXT,
               topics_ratings TEXT,
               saved_at TEXT)'''
    )

    # --- THIS IS THE CORRECTED TABLE DEFINITION ---
    # The 'group_id' column now has a UNIQUE constraint.
    c.execute(
        '''CREATE TABLE IF NOT EXISTS analysis_results (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               group_id INTEGER UNIQUE,
               analysis TEXT,
               timetable TEXT,
               roadmap TEXT,
               timestamp TEXT,
               FOREIGN KEY(group_id) REFERENCES file_groups(id))'''
    )

    c.execute(
        '''CREATE TABLE IF NOT EXISTS chat_sessions (
               id TEXT PRIMARY KEY,
               user_id INTEGER,
               group_id INTEGER,
               title TEXT,
               created_at TEXT)'''
    )

    c.execute(
        '''CREATE TABLE IF NOT EXISTS chat_history (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER,
               group_id INTEGER,
               session_id TEXT,
               role TEXT,
               message TEXT,
               timestamp TEXT,
               FOREIGN KEY(user_id) REFERENCES users(id),
               FOREIGN KEY(group_id) REFERENCES file_groups(id),
               FOREIGN KEY(session_id) REFERENCES chat_sessions(id))'''
    )

    try: c.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT")
    except Exception: pass


    c.execute(
        '''CREATE TABLE IF NOT EXISTS chat_history_image (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER,
               group_id INTEGER,
               session_id TEXT,
               image_id TEXT,
               image_path TEXT,
               role TEXT,
               message TEXT,
               timestamp TEXT,
               FOREIGN KEY(user_id) REFERENCES users(id),
               FOREIGN KEY(group_id) REFERENCES file_groups(id),
               FOREIGN KEY(session_id) REFERENCES chat_sessions(id))'''
    )
    try: c.execute("ALTER TABLE chat_history_image ADD COLUMN session_id TEXT")
    except Exception: pass

    c.execute(
        '''CREATE TABLE IF NOT EXISTS chat_history_video (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER,
               group_id INTEGER,
               session_id TEXT,
               video_id TEXT,
               video_url TEXT,
               role TEXT,
               message TEXT,
               timestamp TEXT,
               FOREIGN KEY(user_id) REFERENCES users(id),
               FOREIGN KEY(group_id) REFERENCES file_groups(id),
               FOREIGN KEY(session_id) REFERENCES chat_sessions(id))'''
    )
    try: c.execute("ALTER TABLE chat_history_video ADD COLUMN session_id TEXT")
    except Exception: pass

    c.execute(
        '''CREATE TABLE IF NOT EXISTS session_history (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER,
               group_id INTEGER,
               action TEXT,
               timestamp TEXT,
               details TEXT,
               FOREIGN KEY(user_id) REFERENCES users(id),
               FOREIGN KEY(group_id) REFERENCES file_groups(id))'''
    )
    c.execute(
        '''CREATE TABLE IF NOT EXISTS quiz_results (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER,
               group_id INTEGER,
               subject TEXT,
               quiz_date TEXT,
               total_marks REAL,
               details TEXT,
               FOREIGN KEY(user_id) REFERENCES users(id),
               FOREIGN KEY(group_id) REFERENCES file_groups(id))'''
    )

    conn.commit()
    return conn


conn = init_db()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def log_action(user_id: Optional[int], group_id: Optional[int], action: str, details: str = "") -> None:
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute(
        "INSERT INTO session_history (user_id, group_id, action, timestamp, details) VALUES (?, ?, ?, ?, ?)",
        (user_id, group_id, action, timestamp, details),
    )
    conn.commit()


def get_group_report_text(group_id: int) -> str:
    c = conn.cursor()
    c.execute("SELECT file_content FROM files WHERE group_id=?", (group_id,))
    files_data = c.fetchall()
    report = ""
    for (file_content,) in files_data:
        try:
            if isinstance(file_content, bytes):
                report += file_content.decode("utf-8") + "\n"
            else:
                report += str(file_content) + "\n"
        except Exception:
            report += str(file_content) + "\n"
    return report
