import json
import traceback
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Query

from ..db import conn, log_action
from ..schemas import (
    QuizGenerateRequest,
    QuizModelResponse,
    QuizGradeRequest,
    QuizGradeResponse,
    QuizSaveRequest,
)
from ..services.gemini import generate_quiz_json


router = APIRouter(prefix="/quizzes", tags=["quiz"])


@router.post("/groups/{group_id}/generate", response_model=QuizModelResponse)
def generate_quiz(group_id: int, req: QuizGenerateRequest):
    c = conn.cursor()
    c.execute("SELECT COALESCE(extracted_text, file_content) FROM files WHERE group_id=?", (group_id,))
    rows = c.fetchall()
    report = "".join([r[0] if isinstance(r[0], str) else str(r[0]) for r in rows])
    
    c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (group_id,))
    row = c.fetchone()
    syllabus = row[0] if row else ""
    
    # Check if we have files (report)
    if not report:
        raise HTTPException(status_code=400, detail="No files found for this group. Please upload study materials first.")
    
    # If no syllabus, provide a default one based on the subject
    if not syllabus:
        syllabus = f"""
        Course: {req.subject}
        
        This is a general syllabus for {req.subject}. Topics may include:
        - Fundamental concepts and principles
        - Core theories and methodologies  
        - Practical applications and examples
        - Problem-solving techniques
        - Current trends and developments
        
        Learning objectives:
        - Understand key concepts in {req.subject}
        - Apply theoretical knowledge to practical problems
        - Analyze and evaluate different approaches
        - Demonstrate proficiency in core skills
        """
    
    try:
        print(f"DEBUG: Generating quiz for group_id={group_id}, subject={req.subject}")
        print(f"DEBUG: Report length: {len(report)}, Syllabus length: {len(syllabus)}")
        
        data = generate_quiz_json(report, syllabus, req.subject)
        print(f"DEBUG: Quiz data generated: {data}")
        
        return QuizModelResponse(
            subject=req.subject,
            questions=data.get("questions", []),
            options=data.get("options", []),
            answers=data.get("answers", []),
            explanations=data.get("explanations", []) or data.get("expanation", []),
        )
    except Exception as e:
        print(f"ERROR: Quiz generation failed with exception: {str(e)}")
        print(f"ERROR: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@router.post("/grade", response_model=QuizGradeResponse)
def grade_quiz(req: QuizGradeRequest):
    marks: List[float] = []
    for correct, user in zip(req.correct_answers, req.user_answers):
        marks.append(1.0 if (str(correct).strip().lower() == str(user).strip().lower()) else 0.0)
    tot_mark = float(sum(marks))
    return QuizGradeResponse(marks=marks, tot_mark=tot_mark)


@router.post("/groups/{group_id}/save")
def save_quiz_result(group_id: int, user_id: int = Query(...), body: QuizSaveRequest = None):
    if body is None:
        raise HTTPException(status_code=400, detail="Missing body")
    c = conn.cursor()
    quiz_date = datetime.now().isoformat()
    c.execute(
        "INSERT INTO quiz_results (user_id, group_id, subject, quiz_date, total_marks, details) VALUES (?, ?, ?, ?, ?, ?)",
        (
            user_id,
            group_id,
            body.subject,
            quiz_date,
            float(sum(body.marks)),
            json.dumps(body.dict()),
        ),
    )
    conn.commit()
    log_action(user_id, group_id, "quiz", f"Quiz on {body.subject} scored {float(sum(body.marks))}")
    return {"status": "ok"}


@router.get("/groups/{group_id}")
def list_quiz_results(group_id: int, user_id: int = Query(...)):
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


