from datetime import datetime
import json
from fastapi import APIRouter

from ..db import conn
from ..schemas import SyllabusContent


router = APIRouter(tags=["syllabus"])


@router.get("/courses/{course_id}/syllabus")
def get_course_syllabus(course_id: str):
    c = conn.cursor()
    c.execute("SELECT syllabus_content, saved_at FROM syllabus WHERE course_id=?", (course_id,))
    row = c.fetchone()
    if not row:
        return {"syllabus_content": "", "saved_at": None}
    return {"syllabus_content": row[0], "saved_at": row[1]}


@router.put("/courses/{course_id}/syllabus")
def save_course_syllabus(course_id: str, body: SyllabusContent):
    c = conn.cursor()
    saved_at = datetime.now().isoformat()
    c.execute(
        "UPDATE syllabus SET syllabus_content=?, saved_at=? WHERE course_id=?",
        (body.syllabus_content, saved_at, course_id),
    )
    if c.rowcount == 0:
        c.execute(
            "INSERT INTO syllabus (course_id, syllabus_content, saved_at) VALUES (?, ?, ?)",
            (course_id, body.syllabus_content, saved_at),
        )
    conn.commit()
    return {"status": "ok", "saved_at": saved_at}


@router.get("/groups/{group_id}/syllabus")
def get_group_syllabus(group_id: int):
    c = conn.cursor()
    c.execute("SELECT syllabus_content, topics_ratings, saved_at FROM syllabus_for_students WHERE group_id=?", (group_id,))
    row = c.fetchone()
    if not row:
        return {"syllabus_content": "", "ratings": {}, "saved_at": None}
    content, ratings, saved_at = row
    try:
        ratings_json = json.loads(ratings) if ratings else {}
    except Exception:
        ratings_json = {}
    return {"syllabus_content": content or "", "ratings": ratings_json, "saved_at": saved_at}


@router.put("/groups/{group_id}/syllabus")
def save_group_syllabus(group_id: int, body: SyllabusContent):
    c = conn.cursor()
    saved_at = datetime.now().isoformat()
    c.execute(
        "UPDATE syllabus_for_students SET syllabus_content=?, topics_ratings=?, saved_at=? WHERE group_id=?",
        (body.syllabus_content, json.dumps(body.ratings or {}), saved_at, group_id),
    )
    if c.rowcount == 0:
        c.execute(
            "INSERT INTO syllabus_for_students (group_id, syllabus_content, topics_ratings, saved_at) VALUES (?, ?, ?, ?)",
            (group_id, body.syllabus_content, json.dumps(body.ratings or {}), saved_at),
        )
    conn.commit()
    return {"status": "ok", "saved_at": saved_at}


