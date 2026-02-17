from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException

from ..db import conn, log_action
from ..schemas import CreateGroupRequest, FileResponse

try:
    import fitz
except Exception:
    fitz = None


router = APIRouter(tags=["groups-files"])


@router.get("/users/{user_id}/groups")
def get_user_groups(user_id: int):
    c = conn.cursor()
    c.execute("SELECT id, group_name FROM file_groups WHERE user_id=?", (user_id,))
    groups = c.fetchall()
    return [{"id": gid, "group_name": gname} for gid, gname in groups]


@router.post("/users/{user_id}/groups")
def create_group(user_id: int, req: CreateGroupRequest):
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute(
        "INSERT INTO file_groups (user_id, group_name, created_at) VALUES (?, ?, ?)",
        (user_id, req.group_name, created_at),
    )
    conn.commit()
    log_action(user_id, c.lastrowid, "create_group", f"Created group: {req.group_name}")
    return {"status": "ok", "group_id": c.lastrowid}


def read_pdf_bytes(data: bytes) -> str:
    if fitz is None:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    text = ""
    doc = fitz.open(stream=data, filetype="pdf")
    for p in doc:
        text += p.get_text()
    return text


@router.post("/groups/{group_id}/files", response_model=FileResponse)
async def upload_file(group_id: int, file: UploadFile = File(...)):
    raw = await file.read()
    if file.content_type == "text/plain":
        try:
            content = raw.decode("utf-8")
        except Exception:
            content = raw.decode("latin-1", errors="ignore")
    elif file.content_type == "application/pdf":
        content = read_pdf_bytes(raw)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    c = conn.cursor()
    uploaded_at = datetime.now().isoformat()
    c.execute(
        "INSERT INTO files (group_id, file_name, file_type, file_content, uploaded_at) VALUES (?, ?, ?, ?, ?)",
        (group_id, file.filename, file.content_type, content, uploaded_at),
    )
    conn.commit()
    return FileResponse(id=c.lastrowid, file_name=file.filename, file_type=file.content_type, uploaded_at=uploaded_at)


@router.get("/groups/{group_id}/files", response_model=List[FileResponse])
def list_files(group_id: int):
    c = conn.cursor()
    c.execute("SELECT id, file_name, file_type, uploaded_at FROM files WHERE group_id=?", (group_id,))
    rows = c.fetchall()
    return [FileResponse(id=r[0], file_name=r[1], file_type=r[2], uploaded_at=r[3]) for r in rows]


@router.delete("/files/{file_id}")
def delete_file(file_id: int):
    c = conn.cursor()
    c.execute("DELETE FROM files WHERE id=?", (file_id,))
    conn.commit()
    return {"status": "ok"}


