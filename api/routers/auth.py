from fastapi import APIRouter, HTTPException

from ..db import conn, hash_password, log_action
from ..schemas import LoginRequest, LoginResponse, ChangePasswordRequest


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    c = conn.cursor()
    
    # 1. Validate Admin Code
    c.execute("SELECT id FROM admin_users WHERE admin_code=?", (req.admin_code,))
    admin_row = c.fetchone()
    if not admin_row:
         raise HTTPException(status_code=401, detail="Invalid Admin Code")
    admin_id = admin_row[0]

    # 2. Validate User Credentials
    c.execute(
        "SELECT id, username, course_id, education_level, admin_id FROM users WHERE username=? AND password=?",
        (req.username, hash_password(req.password)),
    )
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id, username, course_id, education_level, user_admin_id = row
    
    # 3. Security Check: User must belong to this admin (or be unassigned legacy user)
    # If user_admin_id is set, it must match.
    if user_admin_id is not None and user_admin_id != admin_id:
         raise HTTPException(status_code=403, detail="User does not belong to this Admin Organization")

    # Optional: Link legacy user to this admin on first valid login?
    # For now, let's just proceed.

    log_action(user_id, None, "login", "User logged in")
    return LoginResponse(user_id=user_id, username=username, course_id=course_id, education_level=education_level)


@router.post("/change-password")
def change_password(req: ChangePasswordRequest):
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE id=?", (hash_password(req.new_password), req.user_id))
    conn.commit()
    return {"status": "ok"}


# Admin user creation moved to admin router


