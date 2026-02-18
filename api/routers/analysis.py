from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..db import conn
from ..schemas import AnalysisResponse
from ..services.gemini import analyze_report, generate_timetable, generate_roadmap

router = APIRouter(prefix="/groups", tags=["analysis"])


def save_analysis_result(group_id: int, analysis: str, timetable: str, roadmap: str):
    """Saves or updates the analysis results for a given group."""
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute(
        """
        INSERT INTO analysis_results (group_id, analysis, timetable, roadmap, timestamp) 
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(group_id) DO UPDATE SET
        analysis=excluded.analysis,
        timetable=excluded.timetable,
        roadmap=excluded.roadmap,
        timestamp=excluded.timestamp;
        """,
        (group_id, analysis, timetable, roadmap, timestamp),
    )
    conn.commit()

@router.post("/{group_id}/analysis")
def perform_analysis(group_id: int):
    c = conn.cursor()
    c.execute("SELECT COALESCE(extracted_text, file_content) FROM files WHERE group_id=?", (group_id,))
    report_rows = c.fetchall()
    if not report_rows:
        raise HTTPException(status_code=400, detail="No report files found for this group.")
    report = "".join([row[0] for row in report_rows])

    c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (str(group_id),))
    syllabus_row = c.fetchone()
    if not syllabus_row or not syllabus_row[0]:
        raise HTTPException(status_code=400, detail="No syllabus found for this group.")
    syllabus = syllabus_row[0]

    try:
        analysis_text = analyze_report(report)
        timetable_text = generate_timetable(report, syllabus)
        roadmap_text = generate_roadmap(report, syllabus)

        if not all([analysis_text, timetable_text, roadmap_text]):
             raise HTTPException(status_code=500, detail="AI service failed to generate a complete analysis.")

        save_analysis_result(group_id, analysis_text, timetable_text, roadmap_text)
        
        return {
            "analysis": analysis_text,
            "timetable": timetable_text,
            "roadmap": roadmap_text,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during AI generation: {e}")


@router.get("/{group_id}/analysis")
def get_latest_analysis(group_id: int):
    c = conn.cursor()
    c.execute(
        "SELECT analysis, timetable, roadmap, timestamp FROM analysis_results WHERE group_id=? ORDER BY timestamp DESC LIMIT 1",
        (group_id,),
    )
    row = c.fetchone()
    if not row:
        return None
    return AnalysisResponse(analysis=row[0], timetable=row[1], roadmap=row[2], timestamp=row[3])

@router.get("/{group_id}/status")
def get_analysis_status(group_id: int):
    """Checks if a group has the necessary components for an analysis."""
    c = conn.cursor()
    
    c.execute("SELECT EXISTS(SELECT 1 FROM files WHERE group_id=?)", (group_id,))
    has_report = c.fetchone()[0] == 1

    c.execute("SELECT EXISTS(SELECT 1 FROM syllabus_for_students WHERE group_id=?)", (str(group_id),))
    has_syllabus = c.fetchone()[0] == 1
    
    return {
        "has_report": has_report,
        "has_syllabus": has_syllabus
    }
