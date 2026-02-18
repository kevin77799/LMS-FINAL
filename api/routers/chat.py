import os
import re
from datetime import datetime
from typing import List, Optional
import urllib.request

import requests
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi

from ..db import conn
from ..schemas import ChatTextRequest, ChatResponse, ChatHistoryItem, VideoChatRequest, ChatSession

try:
    from PIL import Image
except Exception:
    Image = None

try:
    import google.generativeai as genai
except Exception:
    genai = None


router = APIRouter(prefix="/chat", tags=["chat"])


def get_local_path(filename: str) -> str:
    safe_filename = os.path.basename(filename).replace(" ", "_")
    downloads_folder = os.path.join("downloads")
    os.makedirs(downloads_folder, exist_ok=True)
    return os.path.join(downloads_folder, safe_filename)


def chatbot_text_response(user_message: str, syllabus: str = "", analysis_text: str = "") -> str:
    if not genai:
        return "[Gemini not installed]"
    mod = genai.GenerativeModel(
        model_name='gemini-2.0-flash',
        system_instruction=(
            "You are an educational assistant chatbot. Answer clearly and in depth based on the student's analysis and syllabus. "
            "You can use your own knowledge and web search to provide a comprehensive response. "
            "Your entire response must be in plain text. Do not use any Markdown formatting like asterisks for bolding or bullet points."
        ),
    )
    prompt = (
        f"Answer the user's question: {user_message}\n"
        f"With respect to the Syllabus: {syllabus}\n"
        f"Analysis of the student: {analysis_text}\n"
    )
    resp = mod.generate_content(prompt)
    return getattr(resp, "text", "") or ""


@router.get("/sessions", response_model=List[ChatSession])
def list_chat_sessions(user_id: int = Query(...), group_id: int = Query(...)):
    c = conn.cursor()
    c.execute(
        "SELECT id, user_id, group_id, title, created_at FROM chat_sessions WHERE user_id=? AND group_id=? ORDER BY created_at DESC",
        (user_id, group_id)
    )
    rows = c.fetchall()
    return [ChatSession(id=r[0], user_id=r[1], group_id=r[2], title=r[3], created_at=r[4]) for r in rows]

@router.post("/groups/{group_id}/text", response_model=ChatResponse)
def chat_text(group_id: int, body: ChatTextRequest):
    c = conn.cursor()
    
    # Ensure session exists
    c.execute("SELECT id FROM chat_sessions WHERE id=?", (body.session_id,))
    if not c.fetchone():
        title = body.message[:50] + ("..." if len(body.message) > 50 else "")
        created_at = datetime.now().isoformat()
        c.execute(
            "INSERT INTO chat_sessions (id, user_id, group_id, title, created_at) VALUES (?, ?, ?, ?, ?)",
            (body.session_id, body.user_id, group_id, title, created_at)
        )

    c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (group_id,))
    row = c.fetchone()
    syllabus = row[0] if row else ""
    c.execute(
        "SELECT analysis FROM analysis_results WHERE group_id=? ORDER BY timestamp DESC LIMIT 1",
        (group_id,),
    )
    row = c.fetchone()
    analysis_text = row[0] if row else ""
    
    response = chatbot_text_response(body.message, syllabus, analysis_text)
    timestamp = datetime.now().isoformat()
    
    c.execute(
        "INSERT INTO chat_history (user_id, group_id, session_id, role, message, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (body.user_id, group_id, body.session_id, "user", body.message, timestamp),
    )
    c.execute(
        "INSERT INTO chat_history (user_id, group_id, session_id, role, message, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (body.user_id, group_id, body.session_id, "assistant", response, timestamp),
    )
    conn.commit()
    return ChatResponse(response=response)


@router.get("/groups/{group_id}/text", response_model=List[ChatHistoryItem])
def chat_text_history(group_id: int, user_id: int = Query(...), session_id: Optional[str] = Query(None)):
    c = conn.cursor()
    if session_id:
        c.execute(
            "SELECT role, message, timestamp FROM chat_history WHERE user_id=? AND group_id=? AND session_id=? ORDER BY timestamp",
            (user_id, group_id, session_id),
        )
    else:
        # Fallback to general history (backwards compatibility)
        c.execute(
            "SELECT role, message, timestamp FROM chat_history WHERE user_id=? AND group_id=? AND session_id IS NULL ORDER BY timestamp",
            (user_id, group_id),
        )
    rows = c.fetchall()
    return [ChatHistoryItem(role=r[0], message=r[1], timestamp=r[2]) for r in rows]


@router.post("/groups/{group_id}/image", response_model=ChatResponse)
async def chat_image(group_id: int, session_id: str = Form(...), user_id: int = Form(...), message: str = Form(""), image: UploadFile = File(None), image_url: str = Form(None)):
    if Image is None or not genai:
        raise HTTPException(status_code=500, detail="Image or Gemini dependencies not installed")

    c = conn.cursor()
    c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (group_id,))
    row = c.fetchone()
    syllabus = row[0] if row else ""
    c.execute(
        "SELECT analysis FROM analysis_results WHERE group_id=? ORDER BY timestamp DESC LIMIT 1",
        (group_id,),
    )
    row = c.fetchone()
    analysis_text = row[0] if row else ""

    img_path: Optional[str] = None
    if image is not None:
        data = await image.read()
        img_path = get_local_path(image.filename)
        with open(img_path, "wb") as f:
            f.write(data)
    elif image_url:
        resp = requests.get(image_url, timeout=20)
        resp.raise_for_status()
        filename = os.path.basename(image_url) or "image.jpg"
        img_path = get_local_path(filename)
        with open(img_path, "wb") as f:
            f.write(resp.content)
    else:
        raise HTTPException(status_code=400, detail="Provide image file or image_url")

    img_for_model = Image.open(img_path)
    mod = genai.GenerativeModel(
        model_name='gemini-2.0-flash',
        system_instruction=(
            "You are an educational assistant chatbot. Answer about the given image with respect to the syllabus and student analysis. "
            "You can use your own knowledge and web search to provide a comprehensive response. "
            "Your entire response must be in plain text. Do not use any Markdown formatting like asterisks for bolding or bullet points."
        ),
    )
    prompt_text = (
        "Answer the question from the given image with respect to the student's syllabus and analysis.\n"
        f"Syllabus: {syllabus}\n"
        f"Question: {message}\n"
        f"Analysis: {analysis_text}\n"
    )
    resp = mod.generate_content([prompt_text, img_for_model])
    answer = getattr(resp, "text", "") or ""

    image_id = img_path
    timestamp = datetime.now().isoformat()
    c.execute(
        "INSERT INTO chat_history_image (user_id, group_id, session_id, image_id, image_path, role, message, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, group_id, session_id, image_id, img_path, "user", message, timestamp),
    )
    c.execute(
        "INSERT INTO chat_history_image (user_id, group_id, session_id, image_id, image_path, role, message, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, group_id, session_id, image_id, img_path, "assistant", answer, timestamp),
    )

    conn.commit()
    return ChatResponse(response=answer)


@router.get("/groups/{group_id}/image/{image_id}", response_model=List[ChatHistoryItem])
def chat_image_history(group_id: int, image_id: str, user_id: int = Query(...), session_id: Optional[str] = Query(None)):
    c = conn.cursor()
    if session_id:
        c.execute(
            "SELECT role, message, timestamp FROM chat_history_image WHERE user_id=? AND group_id=? AND image_id=? AND session_id=? ORDER BY id",
            (user_id, group_id, image_id, session_id),
        )
    else:
        c.execute(
            "SELECT role, message, timestamp FROM chat_history_image WHERE user_id=? AND group_id=? AND image_id=? AND session_id IS NULL ORDER BY id",
            (user_id, group_id, image_id),
        )
    rows = c.fetchall()
    return [ChatHistoryItem(role=r[0], message=r[1], timestamp=r[2]) for r in rows]


def extract_video_id(url: str) -> Optional[str]:
    """
    Extracts the video ID from various YouTube URL formats, including standard, shortened, embed, and shorts.
    """
    # Using a raw string (r"...") to prevent syntax warnings
    regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

def get_youtube_video_title(url: str) -> str:
    """Fetches the title of a YouTube video from its URL."""
    try:
        # Use requests which is more robust than urllib
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            html = resp.text
            title_search = re.search(r"<title>(.*?)</title>", html)
            if title_search:
                title = title_search.group(1).replace(" - YouTube", "").strip()
                return title
    except Exception as e:
        print(f"Could not fetch video title for {url}: {e}")
    return "Unknown Title"


@router.post("/groups/{group_id}/video", response_model=ChatResponse)
def chat_video(group_id: int, body: VideoChatRequest):
    if not genai:
        raise HTTPException(status_code=500, detail="Gemini not available")

    vid = extract_video_id(body.video_url)
    if not vid:
        raise HTTPException(status_code=400, detail="Invalid or unsupported YouTube URL.")

    # ... (db queries skipped for brevity in replacement, assuming context lines match)

    c = conn.cursor()
    c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (group_id,))
    row = c.fetchone()
    syllabus = row[0] if row else ""
    c.execute(
        "SELECT analysis FROM analysis_results WHERE group_id=? ORDER BY timestamp DESC LIMIT 1",
        (group_id,),
    )
    row = c.fetchone()
    analysis_text = row[0] if row else ""

    video_title = get_youtube_video_title(body.video_url)
    context_for_prompt = ""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(vid)
        transcript_text = ' '.join([i['text'] for i in transcript])
        context_for_prompt = f"Context from Video Transcript: {transcript_text}"
    except AttributeError:
        # Debugging the weird 'no attribute' error
        print(f"DEBUG: YouTubeTranscriptApi attributes: {dir(YouTubeTranscriptApi)}")
        context_for_prompt = (
             "Context: The transcript for this video is unavailable (API Error). "
             "Please answer the user's question about the video using your general knowledge and web search capabilities. "
             f"The video title is '{video_title}'."
        )
    except Exception as e:
        print(f"Could not fetch transcript for video {vid}: {e}")
        context_for_prompt = (
            "Context: The transcript for this video is unavailable. "
            "Please answer the user's question about the video using your general knowledge and web search capabilities. "
            f"The video title might be '{video_title}'."
        )

    mod = genai.GenerativeModel(
        model_name='gemini-2.0-flash',
        system_instruction=(
            "You are an educational assistant chatbot. Answer the user's question clearly and in depth based on the syllabus, "
            "student analysis, and the video's context. "
            "You can use your own knowledge and web search to provide a comprehensive response. "
            "Your entire response must be in plain text. Do not use any Markdown formatting like asterisks for bolding or bullet points."
        ),
    )
    prompt = (
        "Answer the question from the given context with respect to the syllabus and analysis.\n"
        f"Syllabus: {syllabus}\n"
        f"Question: {body.message}\n"
        f"{context_for_prompt}\n"
        f"Analysis: {analysis_text}\n"
    )
    resp = mod.generate_content(prompt)
    answer = getattr(resp, "text", "") or ""

    timestamp = datetime.now().isoformat()
    c.execute(
        "INSERT INTO chat_history_video (user_id, group_id, session_id, video_id, video_url, role, message, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (body.user_id, group_id, body.session_id, vid, body.video_url, "user", body.message, timestamp),
    )
    c.execute(
        "INSERT INTO chat_history_video (user_id, group_id, session_id, video_id, video_url, role, message, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (body.user_id, group_id, body.session_id, vid, body.video_url, "assistant", answer, timestamp),
    )

    conn.commit()
    return ChatResponse(response=answer)


@router.get("/groups/{group_id}/video/{video_id}", response_model=List[ChatHistoryItem])
def chat_video_history(group_id: int, video_id: str, user_id: int = Query(...), session_id: Optional[str] = Query(None)):
    c = conn.cursor()
    if session_id:
        c.execute(
            "SELECT role, message, timestamp FROM chat_history_video WHERE user_id=? AND group_id=? AND video_id=? AND session_id=? ORDER BY id",
            (user_id, group_id, video_id, session_id),
        )
    else:
        c.execute(
            "SELECT role, message, timestamp FROM chat_history_video WHERE user_id=? AND group_id=? AND video_id=? AND session_id IS NULL ORDER BY id",
            (user_id, group_id, video_id),
        )
    rows = c.fetchall()
    return [ChatHistoryItem(role=r[0], message=r[1], timestamp=r[2]) for r in rows]
