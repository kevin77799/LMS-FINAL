from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile, Response
from typing import List, Union, Optional
from datetime import datetime
from ..db import conn
from ..schemas import (
    UpdateCreateRequest, 
    PollCreateRequest, 
    VoteRequest, 
    UpdateResponse, 
    PollResponse, 
    PollOptionResponse
)
import json

router = APIRouter(tags=["updates"])

# --- Admin Endpoints ---

@router.post("/admin/updates", response_model=UpdateResponse)
async def create_update(
    course_id: str = Form(...),
    content: str = Form(...),
    external_url: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    image_data = await image.read() if image else None
    
    # Store image_data in the new BLOB column
    c.execute(
        "INSERT INTO updates (course_id, content, external_url, image_data, created_at) VALUES (?, ?, ?, ?, ?)",
        (course_id, content, external_url, image_data, created_at)
    )
    conn.commit()
    update_id = c.lastrowid
    
    return UpdateResponse(
        id=update_id, 
        content=content, 
        image_url=f"/updates/{update_id}/image" if image_data else None,
        external_url=external_url, 
        created_at=created_at
    )

@router.get("/updates/{update_id}/image")
def get_update_image(update_id: int):
    c = conn.cursor()
    c.execute("SELECT image_data FROM updates WHERE id=?", (update_id,))
    row = c.fetchone()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Return binary as image
    return Response(content=row[0], media_type="image/jpeg")

@router.post("/admin/polls", response_model=PollResponse)
def create_poll(req: PollCreateRequest):
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    
    # 1. Create Poll
    c.execute(
        "INSERT INTO polls (course_id, question, created_at) VALUES (?, ?, ?)",
        (req.course_id, req.question, created_at)
    )
    poll_id = c.lastrowid
    
    # 2. Create Options
    options_resp = []
    for opt in req.options:
        c.execute(
            "INSERT INTO poll_options (poll_id, option_text) VALUES (?, ?)",
            (poll_id, opt.option_text)
        )
        options_resp.append(PollOptionResponse(id=c.lastrowid, text=opt.option_text, votes=0))
        
    conn.commit()
    
    return PollResponse(
        id=poll_id,
        question=req.question,
        options=options_resp,
        created_at=created_at
    )

# --- Student/Public Endpoints ---
# Note: These don't have the /admin prefix, so we'll mount purely as a separate router or handle prefix manually

@router.get("/courses/{course_id}/updates", response_model=List[Union[UpdateResponse, PollResponse]], tags=["student"])
def get_course_updates(course_id: str, user_id: Optional[int] = None):
    c = conn.cursor()
    combined = []
    
    # 1. Fetch Updates
    try:
        c.execute("SELECT id, content, image_data, external_url, created_at FROM updates WHERE course_id=? ORDER BY created_at DESC", (course_id,))
        for row in c.fetchall():
            update_id = row[0]
            has_image = row[2] is not None
            combined.append(UpdateResponse(
                id=update_id, 
                content=row[1], 
                image_url=f"/updates/{update_id}/image" if has_image else None,
                external_url=row[3], 
                created_at=row[4]
            ))
    except Exception as e:
        print(f"Error fetching updates: {e}")
        
    # 2. Fetch Polls
    try:
        c.execute("SELECT id, question, created_at FROM polls WHERE course_id=? ORDER BY created_at DESC", (course_id,))
        polls = c.fetchall()
        
        for p_row in polls:
            poll_id = p_row[0]
            question = p_row[1]
            p_created_at = p_row[2]
            
            # Get Options & Vote Counts
            c.execute("""
                SELECT o.id, o.option_text, COALESCE(COUNT(v.id), 0) as vote_count 
                FROM poll_options o 
                LEFT JOIN poll_votes v ON o.id = v.option_id 
                WHERE o.poll_id=? 
                GROUP BY o.id
            """, (poll_id,))
            
            options_data = c.fetchall()
            options = []
            if options_data:
                for o_row in options_data:
                    options.append(PollOptionResponse(id=o_row[0], text=o_row[1], votes=o_row[2]))
            
            # Check if user voted
            user_voted_option_id = None
            if user_id:
                c.execute("SELECT option_id FROM poll_votes WHERE user_id=? AND poll_id=?", (user_id, poll_id))
                vote_row = c.fetchone()
                if vote_row:
                    user_voted_option_id = vote_row[0]
                    
            combined.append(PollResponse(
                id=poll_id,
                question=question,
                options=options,
                user_voted_option_id=user_voted_option_id,
                created_at=p_created_at
            ))
    except Exception as e:
        print(f"Error fetching polls: {e}")
        
    # Sort combined list by created_at desc
    combined.sort(key=lambda x: x.created_at, reverse=True)
    
    return combined

@router.post("/polls/vote", tags=["student"])
def vote_poll(req: VoteRequest):
    c = conn.cursor()
    
    # Verify option exists and get poll_id
    c.execute("SELECT poll_id FROM poll_options WHERE id=?", (req.option_id,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Option not found")
    poll_id = row[0]
    
    # Check if user already voted in this poll
    # (Checking against poll_votes table where poll_id = X and user_id = Y)
    # The UNIQUE constraint on (poll_id, user_id) handles this, but explicit check is nicer error message
    c.execute("SELECT id FROM poll_votes WHERE poll_id=? AND user_id=?", (poll_id, req.user_id))
    if c.fetchone():
        raise HTTPException(status_code=400, detail="Already voted in this poll")

    try:
        c.execute(
            "INSERT INTO poll_votes (poll_id, option_id, user_id) VALUES (?, ?, ?)",
            (poll_id, req.option_id, req.user_id)
        )
        conn.commit()
        return {"status": "ok"}
    except Exception as e:
        conn.rollback()
        print(f"Vote error: {e}")
        raise HTTPException(status_code=500, detail="Vote failed")
