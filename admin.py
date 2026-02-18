import streamlit as st
import sqlite3
from datetime import datetime
import hashlib
import fitz # PyMuPDF

def init_db():
    conn = sqlite3.connect("student_analyzer.db", check_same_thread=False)
    # The rest of your init_db function remains the same...
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    course_id TEXT,
                    education_level TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS file_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_name TEXT,
                    created_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS session_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                group_id INTEGER,
                action TEXT,
                timestamp TEXT,
                details TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(group_id) REFERENCES file_groups(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    file_name TEXT,
                    file_type TEXT,
                    file_content BLOB,
                    uploaded_at TEXT,
                    FOREIGN KEY(group_id) REFERENCES file_groups(id))''')
    
    # This table stores the MASTER syllabus for a course
    c.execute('''CREATE TABLE IF NOT EXISTS syllabus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id TEXT UNIQUE,
                    syllabus_content TEXT,
                    saved_at TEXT)''')

    # This table stores the SPECIFIC syllabus for a student's group
    c.execute('''CREATE TABLE IF NOT EXISTS syllabus_for_students (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               group_id TEXT UNIQUE,
               syllabus_content TEXT,
               topics_ratings TEXT,
               saved_at TEXT)''')

    conn.commit()
    return conn

conn = init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(username: str, password: str, course_id: str, education_level: str) -> bool:
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, course_id, education_level) VALUES (?, ?, ?, ?)", 
                  (username, hash_password(password), course_id, education_level))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_all_users():
    c = conn.cursor()
    c.execute("SELECT id, username, course_id FROM users ORDER BY id")
    return c.fetchall()
    
def get_all_course_ids():
    c = conn.cursor()
    c.execute("SELECT DISTINCT course_id FROM users WHERE course_id IS NOT NULL AND course_id != ''")
    return [row[0] for row in c.fetchall()]

def get_user_groups(user_id: int):
    c = conn.cursor()
    c.execute("SELECT id, group_name FROM file_groups WHERE user_id=?", (user_id,))
    return c.fetchall()

def log_action(user_id: int, group_id: int, action: str, details: str):
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO session_history (user_id, group_id, action, timestamp, details) VALUES (?, ?, ?, ?, ?)",
              (user_id, group_id, action, timestamp, details))
    conn.commit()

def read_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# --- SYLLABUS FUNCTIONS FOR ADMIN PANEL (COURSE-SPECIFIC) ---
def get_syllabus_for_course(course_id: str):
    """Fetches the master syllabus for a course."""
    c = conn.cursor()
    c.execute("SELECT syllabus_content, saved_at FROM syllabus WHERE course_id=?", (course_id,))
    return c.fetchone()

def save_syllabus_for_course(course_id: str, syllabus_content: str):
    """Saves or updates the master syllabus for a course."""
    c = conn.cursor()
    saved_at = datetime.now().isoformat()
    c.execute(
        "INSERT OR REPLACE INTO syllabus (course_id, syllabus_content, saved_at) VALUES (?, ?, ?)",
        (course_id, syllabus_content, saved_at)
    )
    conn.commit()


st.set_page_config(page_title="Admin Dashboard", page_icon=":crown:", layout="wide")
st.title("Admin Panel")

tabs = st.tabs(["User Management", "File Management", "Syllabus Management"])

with tabs[0]:
    st.header("Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        new_course_id = st.text_input("Course ID")
        new_education_level = st.selectbox("Select Year", options=["1","2","3","4"], format_func=lambda x: f"Year {x}")
        submitted = st.form_submit_button("Create User")
        if submitted:
            if all([new_username, new_password, new_course_id]):
                if signup_user(new_username, new_password, new_course_id, new_education_level):
                    st.success(f"User '{new_username}' created.")
                else:
                    st.error("Username already exists.")
            else:
                st.error("Please fill in all fields.")

with tabs[1]:
    st.header("File Management")
    all_users = get_all_users()
    if all_users:
        user_options = {user[0]: f"{user[1]} (ID: {user[0]})" for user in all_users}
        selected_user_id = st.selectbox("Select a User", options=list(user_options.keys()), format_func=lambda x: user_options[x])
        
        st.subheader(f"Manage Groups for {user_options[selected_user_id]}")
        # ... (Your existing file and group management UI can go here)

with tabs[2]:
    st.header("Syllabus Management by Course")
    st.info("Here you can assign a master syllabus to an entire course. This syllabus will be used for all student groups within that course.")

    course_ids = get_all_course_ids()
    if not course_ids:
        st.warning("No courses found. Please create a user with a Course ID first.")
    else:
        selected_course_id = st.selectbox(
            "Select a Course ID", 
            options=course_ids,
            key="syllabus_course_select"
        )

        if selected_course_id:
            st.subheader(f"Editing Syllabus for Course: {selected_course_id}")
            
            existing_syllabus_data = get_syllabus_for_course(selected_course_id)
            existing_content = existing_syllabus_data[0] if existing_syllabus_data else ""
            
            syllabus_content = st.text_area(
                "Syllabus Content", 
                value=existing_content, 
                height=300,
                key=f"syllabus_text_{selected_course_id}"
            )

            if st.button("Save Syllabus for this Course"):
                save_syllabus_for_course(selected_course_id, syllabus_content)
                log_action(0, 0, "admin_save_course_syllabus", f"Admin saved syllabus for course {selected_course_id}")
                st.success(f"Syllabus saved for course '{selected_course_id}'!")
