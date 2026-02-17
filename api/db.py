import os
import hashlib
from datetime import datetime
from typing import Optional, Any
import sqlite3

# Import conditionally to avoid errors if not installed locally
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

from .core.config import DB_PATH, DATABASE_URL

class SmartCursor:
    def __init__(self, cursor, is_postgres):
        self.cursor = cursor
        self.is_postgres = is_postgres
        self._lastrowid = None

    def execute(self, query: str, params: Any = None):
        if self.is_postgres:
            # Replace ? with %s for PostgreSQL
            if params:
                query = query.replace('?', '%s')
            
            # lastrowid emulation: Append RETURNING id to INSERT statements
            is_insert = query.strip().upper().startswith("INSERT")
            if is_insert and "RETURNING" not in query.upper():
                query = query.rstrip().rstrip(';') + " RETURNING id"
            
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if is_insert and "RETURNING id" in query:
                row = self.cursor.fetchone()
                if row:
                    self._lastrowid = row[0]
        else:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

    @property
    def lastrowid(self):
        if self.is_postgres:
            return self._lastrowid
        return self.cursor.lastrowid

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def __getattr__(self, name):
        return getattr(self.cursor, name)

class SmartConn:
    def __init__(self, conn, is_postgres):
        self.conn = conn
        self.is_postgres = is_postgres

    def cursor(self):
        return SmartCursor(self.conn.cursor(), self.is_postgres)

    def commit(self):
        return self.conn.commit()

    def rollback(self):
        return self.conn.rollback()

    def close(self):
        return self.conn.close()

    def __getattr__(self, name):
        return getattr(self.conn, name)

def init_db() -> SmartConn:
    is_postgres = False
    if DATABASE_URL:
        try:
            raw_conn = psycopg2.connect(DATABASE_URL)
            is_postgres = True
            print("Connected to PostgreSQL database.")
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}. Falling back to SQLite.")
            raw_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    else:
        raw_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        print(f"Connected to SQLite database at {DB_PATH}")

    conn = SmartConn(raw_conn, is_postgres)
    c = conn.cursor()

    # Define table creation SQL with compatibility adjustments
    def run_create(sql):
        if is_postgres:
            # SQLite specific types to Postgres
            sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            sql = sql.replace('AUTOINCREMENT', '') # Fallback if part of a list
            sql = sql.replace('BLOB', 'BYTEA')
            sql = sql.replace('REAL', 'DOUBLE PRECISION')
        c.execute(sql)

    run_create('''CREATE TABLE IF NOT EXISTS admin_users (
                   id SERIAL PRIMARY KEY,
                   username TEXT UNIQUE,
                   email TEXT,
                   password TEXT,
                   admin_code TEXT UNIQUE)''')

    run_create('''CREATE TABLE IF NOT EXISTS users (
                   id SERIAL PRIMARY KEY,
                   username TEXT UNIQUE,
                   password TEXT,
                   course_id TEXT,
                   education_level TEXT,
                   admin_id INTEGER REFERENCES admin_users(id))''')
    
    # Migrations for existing tables
    try:
        if is_postgres:
            c.execute("ALTER TABLE users ADD COLUMN admin_id INTEGER REFERENCES admin_users(id)")
        else:
            c.execute("ALTER TABLE users ADD COLUMN admin_id INTEGER")
    except Exception: pass

    run_create('''CREATE TABLE IF NOT EXISTS admin_otp (
                   code TEXT PRIMARY KEY,
                   created_at TEXT)''')

    run_create('''CREATE TABLE IF NOT EXISTS file_groups (
                   id SERIAL PRIMARY KEY,
                   user_id INTEGER REFERENCES users(id),
                   group_name TEXT,
                   created_at TEXT)''')

    run_create('''CREATE TABLE IF NOT EXISTS files (
                   id SERIAL PRIMARY KEY,
                   group_id INTEGER REFERENCES file_groups(id),
                   file_name TEXT,
                   file_type TEXT,
                   file_content BYTEA,
                   uploaded_at TEXT)''')

    run_create('''CREATE TABLE IF NOT EXISTS syllabus (
                   id SERIAL PRIMARY KEY,
                   course_id TEXT,
                   syllabus_content TEXT,
                   saved_at TEXT)''')

    run_create('''CREATE TABLE IF NOT EXISTS syllabus_for_students (
                   id SERIAL PRIMARY KEY,
                   group_id TEXT,
                   syllabus_content TEXT,
                   topics_ratings TEXT,
                   saved_at TEXT)''')

    run_create('''CREATE TABLE IF NOT EXISTS analysis_results (
                   id SERIAL PRIMARY KEY,
                   group_id INTEGER UNIQUE REFERENCES file_groups(id),
                   analysis TEXT,
                   timetable TEXT,
                   roadmap TEXT,
                   timestamp TEXT)''')

    run_create('''CREATE TABLE IF NOT EXISTS chat_sessions (
                   id TEXT PRIMARY KEY,
                   user_id INTEGER,
                   group_id INTEGER,
                   title TEXT,
                   created_at TEXT)''')

    run_create('''CREATE TABLE IF NOT EXISTS chat_history (
                   id SERIAL PRIMARY KEY,
                   user_id INTEGER REFERENCES users(id),
                   group_id INTEGER REFERENCES file_groups(id),
                   session_id TEXT REFERENCES chat_sessions(id),
                   role TEXT,
                   message TEXT,
                   timestamp TEXT)''')
    
    try: c.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT")
    except Exception: pass

    run_create('''CREATE TABLE IF NOT EXISTS chat_history_image (
                   id SERIAL PRIMARY KEY,
                   user_id INTEGER REFERENCES users(id),
                   group_id INTEGER REFERENCES file_groups(id),
                   session_id TEXT REFERENCES chat_sessions(id),
                   image_id TEXT,
                   image_path TEXT,
                   role TEXT,
                   message TEXT,
                   timestamp TEXT)''')
    
    try: c.execute("ALTER TABLE chat_history_image ADD COLUMN session_id TEXT")
    except Exception: pass

    run_create('''CREATE TABLE IF NOT EXISTS chat_history_video (
                   id SERIAL PRIMARY KEY,
                   user_id INTEGER REFERENCES users(id),
                   group_id INTEGER REFERENCES file_groups(id),
                   session_id TEXT REFERENCES chat_sessions(id),
                   video_id TEXT,
                   video_url TEXT,
                   role TEXT,
                   message TEXT,
                   timestamp TEXT)''')
    
    try: c.execute("ALTER TABLE chat_history_video ADD COLUMN session_id TEXT")
    except Exception: pass

    run_create('''CREATE TABLE IF NOT EXISTS session_history (
                   id SERIAL PRIMARY KEY,
                   user_id INTEGER REFERENCES users(id),
                   group_id INTEGER REFERENCES file_groups(id),
                   action TEXT,
                   timestamp TEXT,
                   details TEXT)'''
    )
    
    run_create('''CREATE TABLE IF NOT EXISTS quiz_results (
                   id SERIAL PRIMARY KEY,
                   user_id INTEGER REFERENCES users(id),
                   group_id INTEGER REFERENCES file_groups(id),
                   subject TEXT,
                   quiz_date TEXT,
                   total_marks DOUBLE PRECISION,
                   details TEXT)'''
    )

    conn.commit()
    return conn

conn = init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def log_action(user_id: Optional[int], group_id: Optional[int], action: str, details: str = "") -> None:
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    # Handle NULLs correctly in the Tuple
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
                # Handle Postgres memoryview vs SQLite bytes
                if hasattr(file_content, 'tobytes'):
                    report += file_content.tobytes().decode("utf-8") + "\n"
                else:
                    report += file_content.decode("utf-8") + "\n"
            else:
                report += str(file_content) + "\n"
        except Exception:
            report += str(file_content) + "\n"
    return report
