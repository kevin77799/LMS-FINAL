from typing import List
from datetime import datetime
import random
import string

from fastapi import APIRouter, HTTPException, UploadFile, File

from ..db import conn, hash_password, log_action
from ..db import conn, hash_password, log_action
from ..schemas import (
    SignupRequest, 
    CreateGroupRequest, 
    FileResponse, 
    AdminCheckResponse, 
    AdminSetupRequest, 
    AdminGenerateOtpRequest, 
    AdminLoginRequest, 
    AdminLoginResponse
)


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users")
def create_user(req: SignupRequest):
    c = conn.cursor()
    # Check if admin_id is valid
    try:
        if req.admin_id is not None:
             c.execute("SELECT id FROM admin_users WHERE id=?", (req.admin_id,))
             if not c.fetchone():
                  raise HTTPException(status_code=400, detail="Invalid Admin ID")
    except Exception:
         pass 

    try:
        c.execute(
            "INSERT INTO users (username, password, course_id, education_level, admin_id) VALUES (?, ?, ?, ?, ?)",
            (req.username, hash_password(req.password), req.course_id, req.education_level, req.admin_id),
        )
        conn.commit()
        return {"status": "ok", "user_id": c.lastrowid}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail="Username already exists")

# ... existing code ...


@router.get("/users")
def list_users():
    c = conn.cursor()
    c.execute("SELECT id, username, course_id, education_level FROM users ORDER BY id")
    rows = c.fetchall()
    return [
        {"id": r[0], "username": r[1], "course_id": r[2], "education_level": r[3]}
        for r in rows
    ]


@router.get("/courses")
def list_course_ids():
    c = conn.cursor()
    c.execute("SELECT DISTINCT course_id FROM users")
    return [row[0] for row in c.fetchall() if row[0] is not None]


@router.get("/courses/{course_id}/users")
def list_users_by_course(course_id: str):
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE course_id=?", (course_id,))
    rows = c.fetchall()
    return [{"id": r[0], "username": r[1]} for r in rows]


# Admin helpers for groups/files (mirrors UI in admin.py)
@router.get("/users/{user_id}/groups")
def admin_get_user_groups(user_id: int):
    c = conn.cursor()
    c.execute("SELECT id, group_name FROM file_groups WHERE user_id=?", (user_id,))
    groups = c.fetchall()
    return [{"id": gid, "group_name": gname} for gid, gname in groups]


@router.post("/users/{user_id}/groups")
def admin_create_group(user_id: int, req: CreateGroupRequest):
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute(
        "INSERT INTO file_groups (user_id, group_name, created_at) VALUES (?, ?, ?)",
        (user_id, req.group_name, created_at),
    )
    conn.commit()
    log_action(user_id, c.lastrowid, "create_group", f"Created group: {req.group_name} by admin")
    return {"status": "ok", "group_id": c.lastrowid}


def _read_pdf_bytes_or_text(content_type: str, data: bytes) -> str:
    if content_type == "text/plain":
        try:
            return data.decode("utf-8")
        except Exception:
            return data.decode("latin-1", errors="ignore")
    if content_type == "application/pdf":
        try:
            import fitz  # type: ignore
        except Exception:
            raise HTTPException(status_code=500, detail="PyMuPDF not installed")
        text = ""
        doc = fitz.open(stream=data, filetype="pdf")
        for p in doc:
            text += p.get_text()
        return text
    raise HTTPException(status_code=400, detail="Unsupported file type")


@router.post("/groups/{group_id}/files", response_model=FileResponse)
async def admin_upload_file(group_id: int, file: UploadFile = File(...)):
    raw = await file.read()
    content = _read_pdf_bytes_or_text(file.content_type, raw)
    c = conn.cursor()
    uploaded_at = datetime.now().isoformat()
    c.execute(
        "INSERT INTO files (group_id, file_name, file_type, file_content, uploaded_at) VALUES (?, ?, ?, ?, ?)",
        (group_id, file.filename, file.content_type, content, uploaded_at),
    )
    conn.commit()
    return FileResponse(id=c.lastrowid, file_name=file.filename, file_type=file.content_type, uploaded_at=uploaded_at)


@router.get("/groups/{group_id}/files", response_model=List[FileResponse])
def admin_list_files(group_id: int):
    c = conn.cursor()
    c.execute("SELECT id, file_name, file_type, uploaded_at FROM files WHERE group_id=?", (group_id,))
    rows = c.fetchall()
    return [FileResponse(id=r[0], file_name=r[1], file_type=r[2], uploaded_at=r[3]) for r in rows]


@router.delete("/files/{file_id}")
def admin_delete_file(file_id: int):
    c = conn.cursor()
    c.execute("DELETE FROM files WHERE id=?", (file_id,))
    conn.commit()
    return {"status": "ok"}


# Admin syllabus management (course-level)
@router.get("/courses/{course_id}/syllabus")
def admin_get_course_syllabus(course_id: str):
    c = conn.cursor()
    c.execute("SELECT syllabus_content, saved_at FROM syllabus WHERE course_id=?", (course_id,))
    row = c.fetchone()
    if not row:
        return {"syllabus_content": "", "saved_at": None}
    return {"syllabus_content": row[0], "saved_at": row[1]}


@router.put("/courses/{course_id}/syllabus")
def admin_save_course_syllabus(course_id: str, body: dict):
    syllabus_content = body.get("syllabus_content", "")
    c = conn.cursor()
    saved_at = datetime.now().isoformat()
    c.execute(
        "UPDATE syllabus SET syllabus_content=?, saved_at=? WHERE course_id=?",
        (syllabus_content, saved_at, course_id),
    )
    if c.rowcount == 0:
        c.execute(
            "INSERT INTO syllabus (course_id, syllabus_content, saved_at) VALUES (?, ?, ?)",
            (course_id, syllabus_content, saved_at),
        )
    conn.commit()
    return {"status": "ok", "saved_at": saved_at}


# --- Admin Auth ---

@router.get("/auth/check", response_model=AdminCheckResponse)
def check_admin_exists():
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM admin_users")
        count = c.fetchone()[0]
        return {"has_admin": count > 0}
    except Exception:
        # Table might not exist yet if fresh
        return {"has_admin": False}



import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# ... (imports)

def send_email(to_email: str, subject: str, body: str):
    # Debug: Re-load dotenv explicitly to be sure
    load_dotenv()
    
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    # Debugging print
    if not sender_email:
        print(f"[DEBUG] CWD: {os.getcwd()}")
        print(f"[DEBUG] .env exists? {os.path.exists('.env')}")
        print(f"[DEBUG] EMAIL_SENDER is None. All env keys: {[k for k in os.environ.keys() if 'EMAIL' in k]}")

    if not sender_email or not sender_password:
        print("[WARNING] Email credentials not found in .env. OTP printed to console instead.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

@router.post("/auth/generate-otp")
def generate_setup_otp(req: AdminGenerateOtpRequest):
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM admin_users")
        if c.fetchone()[0] > 0:
            raise HTTPException(status_code=403, detail="Admin already exists")
    except Exception:
        pass 
    
    code = ''.join(random.choices(string.digits, k=6))
    
    # Send Email
    email_sent = send_email(
        req.email, 
        "LMS Admin Verification Code", 
        f"Your verification code for Admin Setup is: {code}\n\nThis code expires in 10 minutes."
    )
    
    # Always print to console for dev/fallback
    print(f"\n{'='*40}\n[ADMIN SETUP] VERIFICATION CODE FOR {req.email}: {code}\n{'='*40}\n")
    
    c.execute("DELETE FROM admin_otp") 
    c.execute("INSERT INTO admin_otp (code, created_at) VALUES (?, ?)", (code, datetime.now().isoformat()))
    conn.commit()
    
    msg = f"Verification code sent to {req.email}"
    if not email_sent:
        msg += " (Email failed/not configured. CHECK SERVER CONSOLE)."
        
    return {"message": msg}


@router.post("/auth/setup")
def setup_admin(req: AdminSetupRequest):
    c = conn.cursor()
    
    # 1. Verify OTP
    otp_clean = req.otp.strip()
    
    c.execute("SELECT code FROM admin_otp WHERE code=?", (otp_clean,))
    if not c.fetchone():
        print(f"[DEBUG] Invalid OTP. Received/Clean: '{req.otp}'/'{otp_clean}'")
        raise HTTPException(status_code=400, detail="Invalid Verification Code")
    
    # 2. Create Admin with Code
    try:
        # Check if username taken
        c.execute("SELECT id FROM admin_users WHERE username=?", (req.username,))
        if c.fetchone():
             raise HTTPException(status_code=400, detail="Username already exists")

        # Generate unique code (e.g. ABC-123)
        admin_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        c.execute("INSERT INTO admin_users (username, email, password, admin_code) VALUES (?, ?, ?, ?)", 
                  (req.username, req.email, hash_password(req.password), admin_code))
        c.execute("DELETE FROM admin_otp") # Clear OTP after use
        conn.commit()
    except Exception as e:
         print(e)
         raise HTTPException(status_code=500, detail="Failed to create admin")

    return {"status": "ok", "admin_code": admin_code}


@router.post("/auth/login", response_model=AdminLoginResponse)
def login_admin(req: AdminLoginRequest):
    c = conn.cursor()
    try:
        # Need to handle potential missing column if migration failed silently, but let's assume it worked.
        # Fallback for admin_code is safe.
        c.execute("SELECT id, username, admin_code FROM admin_users WHERE username=? AND password=?", (req.username, hash_password(req.password)))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {"admin_id": row[0], "username": row[1], "admin_code": row[2] or "N/A"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


