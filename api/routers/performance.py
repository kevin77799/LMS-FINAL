import json
from fastapi import APIRouter, Query

from ..db import conn


router = APIRouter(tags=["performance"])


@router.get("/groups/{group_id}/performance")
def performance(group_id: int, user_id: int = Query(...)):
    c = conn.cursor()
    c.execute(
        "SELECT subject, quiz_date, total_marks, details FROM quiz_results WHERE user_id=? AND group_id=? ORDER BY quiz_date",
        (user_id, group_id),
    )
    rows = c.fetchall()
    return [
        {
            "subject": r[0],
            "quiz_date": r[1],
            "total_marks": r[2],
            "details": json.loads(r[3]) if r[3] else {},
        }
        for r in rows
    ]


