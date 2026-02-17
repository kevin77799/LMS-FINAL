import streamlit as st
import sqlite3
import os
import hashlib
import json
import re
import urllib.request
from datetime import datetime
from io import StringIO
import pandas as pd
from PIL import Image
import requests
from urllib.parse import urlparse, parse_qs
from pydantic import BaseModel, Field
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import logging
import google.generativeai as genai
from phi.agent import Agent
from phi.tools.wikipedia import WikipediaTools
from phi.tools.website import WebsiteTools
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.serpapi_tools import SerpApiTools
from phi.model.google import Gemini
from dotenv import load_dotenv
import streamlit.components.v1 as components
import time
import fitz


load_dotenv()
API_KEYS = [os.getenv("GOOGLE_API_KEY_1"), os.getenv("GOOGLE_API_KEY_2"), os.getenv("GOOGLE_API_KEY_3"), os.getenv("GOOGLE_API_KEY_4")]
sa = os.getenv("SERP_API_KEY")

def set_api(index, return_val = False):
    genai.configure(api_key=API_KEYS[index])
    if return_val:
        return API_KEYS[index]

retries = len(API_KEYS)

def init_db():
    conn = sqlite3.connect("student_analyzer.db", check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS file_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_name TEXT,
                    created_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    file_name TEXT,
                    file_type TEXT,
                    file_content BLOB,
                    uploaded_at TEXT,
                    FOREIGN KEY(group_id) REFERENCES file_groups(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS syllabus_for_students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT,
                    syllabus_content TEXT,
                    topics_ratings TEXT,
                    saved_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    analysis TEXT,
                    timetable TEXT,
                    roadmap TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(group_id) REFERENCES file_groups(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_id INTEGER,
                    role TEXT,
                    message TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(group_id) REFERENCES file_groups(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS chat_history_image (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_id INTEGER,
                    image_id TEXT,
                    image_path TEXT,
                    role TEXT,
                    message TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(group_id) REFERENCES file_groups(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS chat_history_video (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_id INTEGER,
                    video_id TEXT,
                    video_url TEXT,
                    role TEXT,
                    message TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(group_id) REFERENCES file_groups(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS session_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_id INTEGER,
                    action TEXT,
                    timestamp TEXT,
                    details TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(group_id) REFERENCES file_groups(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_id INTEGER,
                    subject TEXT,
                    quiz_date TEXT,
                    total_marks REAL,
                    details TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(group_id) REFERENCES file_groups(id))''')
    conn.commit()
    return conn

conn = init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username: str, password: str):
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    result = c.fetchone()
    return result[0] if result else None

def change_password(id, new_password):
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_password), id))
    conn.commit()

def get_user_details(user_id: int):
    c = conn.cursor()
    c.execute("SELECT username, education_level FROM users WHERE id=?", (user_id,))
    return c.fetchone()

def get_user_details_course(user_id: int):
    c = conn.cursor()
    c.execute("SELECT course_id FROM users WHERE id=?", (user_id,))
    return c.fetchone()

def get_user_groups(user_id: int):
    c = conn.cursor()
    c.execute("SELECT id, group_name FROM file_groups WHERE user_id=?", (user_id,))
    return c.fetchall()

def create_file_group(user_id: int, group_name: str):
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute("INSERT INTO file_groups (user_id, group_name, created_at) VALUES (?, ?, ?)", 
              (user_id, group_name, created_at))
    conn.commit()
    return c.lastrowid

def save_file(group_id: int, file_name: str, file_type: str, file_content: bytes):
    c = conn.cursor()
    uploaded_at = datetime.now().isoformat()
    c.execute("INSERT INTO files (group_id, file_name, file_type, file_content, uploaded_at) VALUES (?, ?, ?, ?, ?)",
              (group_id, file_name, file_type, file_content, uploaded_at))
    conn.commit()

def delete_file(fid):
    c = conn.cursor()
    c.execute("DELETE FROM files WHERE id=?", (fid,))
    conn.commit()

def get_syllabus_for_course(course_id: str):
    c = conn.cursor()
    c.execute("SELECT syllabus_content, saved_at FROM syllabus WHERE course_id=?", (course_id,))
    return c.fetchone()

def save_syllabus(group_id: str, syllabus_content: str, topics_ratings: dict):
    c = conn.cursor()
    saved_at = datetime.now().isoformat()
    c.execute("""
        UPDATE syllabus_for_students
        SET syllabus_content = ?,
            topics_ratings = ?,
            saved_at = ?
        WHERE group_id = ?
    """, (syllabus_content, json.dumps(topics_ratings), saved_at, group_id))
    if c.rowcount == 0:
        c.execute("""
            INSERT INTO syllabus_for_students (group_id, syllabus_content, topics_ratings, saved_at)
            VALUES (?, ?, ?, ?)
        """, (group_id, syllabus_content, json.dumps(topics_ratings), saved_at))
    conn.commit()

def save_analysis_result(group_id: int, analysis: str, timetable: str, roadmap: str):
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("""
    UPDATE analysis_results     
    SET analysis = ?,
        timetable = ?,
        roadmap = ?,
        timestamp =?
    WHERE group_id = ?
    """, (analysis, timetable, roadmap, timestamp, group_id))

    if c.rowcount == 0:
        c.execute("""
            INSERT INTO analysis_results (group_id, analysis, timetable, roadmap, timestamp) VALUES (?, ?, ?, ?, ?)""",
              (group_id, analysis, timetable, roadmap, timestamp))        

    conn.commit()
    
def log_action(user_id: int, group_id: int, action: str, details: str = ""):
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO session_history (user_id, group_id, action, timestamp, details) VALUES (?, ?, ?, ?, ?)",
              (user_id, group_id, action, timestamp, details))
    conn.commit()

def save_chat_message(user_id: int, group_id: int, role: str, message: str):
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO chat_history (user_id, group_id, role, message, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, group_id, role, message, timestamp))
    conn.commit()

def get_chat_history(user_id: int, group_id: int):
    c = conn.cursor()
    c.execute("SELECT role, message FROM chat_history WHERE user_id=? AND group_id=? ORDER BY timestamp", (user_id, group_id))
    return c.fetchall()

def delete_chat_history(user_id: int, group_id: int):
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE user_id=? AND group_id=?", (user_id, group_id))
    c.execute("DELETE FROM chat_history_image WHERE user_id=? AND group_id=?", (user_id, group_id))
    c.execute("DELETE FROM chat_history_video WHERE user_id=? AND group_id=?", (user_id, group_id))
    conn.commit()
    log_action(user_id, group_id, "clear_chat_history", "User cleared chat history.")

def get_chat_history_image(user_id, group_id, image_id):
    cur = conn.cursor()
    cur.execute("SELECT role, message FROM chat_history_image WHERE user_id=? AND group_id=? AND image_id=? ORDER BY id",
                (user_id, group_id, image_id))
    return cur.fetchall()

def save_chat_message_image(user_id, group_id, image_id, image_path, role, message):
    cur = conn.cursor()
    timestamp = datetime.now().isoformat()
    cur.execute(
        "INSERT INTO chat_history_image (user_id, group_id, image_id, image_path, role, message, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, group_id, image_id, image_path, role, message, timestamp))
    conn.commit()

def get_chat_history_video(user_id, group_id, video_id):
    cur = conn.cursor()
    cur.execute("SELECT role, message FROM chat_history_video WHERE user_id=? AND group_id=? AND video_id=? ORDER BY id",
                (user_id, group_id, video_id))
    return cur.fetchall()

def save_chat_message_video(user_id, group_id, video_id, video_url, role, message):
    cur = conn.cursor()
    timestamp = datetime.now().isoformat()
    cur.execute(
        "INSERT INTO chat_history_video (user_id, group_id, video_id, video_url, role, message, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, group_id, video_id, video_url, role, message, timestamp))
    conn.commit()    

def get_latest_analysis(group_id: int):
    c = conn.cursor()
    c.execute("SELECT analysis, timetable, roadmap, timestamp FROM analysis_results WHERE group_id=? ORDER BY timestamp DESC LIMIT 1", (group_id,))
    return c.fetchone()

def save_quiz_result(user_id: int, group_id: int, subject: str, total_marks: float, details: dict):
    c = conn.cursor()
    quiz_date = datetime.now().isoformat()
    c.execute("INSERT INTO quiz_results (user_id, group_id, subject, quiz_date, total_marks, details) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, group_id, subject, quiz_date, total_marks, json.dumps(details)))
    conn.commit()

def get_quiz_results(user_id: int, group_id: int):
    c = conn.cursor()
    c.execute("SELECT subject, quiz_date, total_marks, details FROM quiz_results WHERE user_id=? AND group_id=? ORDER BY quiz_date", (user_id, group_id))
    return c.fetchall()

def youtube_video_recommendation(search_keyword: str, min_duration_sec = 30):
    search_keyword = search_keyword.replace(" ", "+")
    try:
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_keyword)
        content = html.read().decode()
        video_ids = re.findall(r"watch\?v=(\S{11})", content)[:300]
        videos = []        
        for vid in list(set(video_ids))[:3]:
            url = f"https://www.youtube.com/watch?v={vid}"
            try:
                video_html = urllib.request.urlopen(url).read().decode()
                duration_match = re.search(r'"lengthSeconds":"(\d+)"', video_html)
                if duration_match:
                    duration_seconds = int(duration_match.group(1))

                    if duration_seconds >= min_duration_sec:
                        title = get_youtube_video_title(url) 
                        videos.append({"id": vid, "title": title})

            except Exception as e:
                print(f"Error fetching or parsing duration for {url}: {e}")
                continue  

        return videos

    except Exception as e:
        return [{"id": "", "title": f"Error: {e}"}]

def get_youtube_video_title(url: str):
    try:
        html = urllib.request.urlopen(url).read().decode()
        title_search = re.search(r"<title>(.*?)</title>", html)
        if title_search:
            title = title_search.group(1).replace(" - YouTube", "").strip()
            return title
    except Exception:
        return "Unknown Title"
    return "Unknown Title"

class Website(BaseModel):
    urls: List[str] = Field(..., description="URLS of the websites")

def website_agents(api_key):
    json_mode_agent = Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=api_key),
        name="Website Agent",
        tools=[WebsiteTools(), WikipediaTools()],
        instructions="Search the web and wikipedia for related topics and provide 5 most popular related content.",
        description="Search the web for related topics and provide 5 most popular related content.",
        response_model=Website,
    )

    json_mode_agent_so = Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=api_key),
        name="Website Agent",
        tools=[WebsiteTools(), WikipediaTools()],
        instructions="Search the web and wikipedia for related topics and provide 5 most popular related content.",
        description="Search the web for related topics and provide 5 most popular related content.",
        response_model=Website,
        structured_output=True
    )

    return json_mode_agent, json_mode_agent_so

def fetch_related_websites(query: str, retries = len(API_KEYS)):
    try:
        api = set_api(0, return_val = True)
        for attempt in range(retries+1):
            try:
                json_model_agent, json_model_agent_so = website_agents(api)
                try:
                    response = json_model_agent.run(query)
                    
                    # Add this print statement to debug
                    print("--- RAW AI RESPONSE FOR WEBSITES ---")
                    print(response)
                    print("------------------------------------")
                    
                    return response.content.urls
                    
                except Exception as e:
                    response = json_model_agent_so.run(query)
                    
                    # Add this print statement to debug
                    print("--- RAW AI RESPONSE FOR WEBSITES (FALLBACK) ---")
                    print(response)
                    print("---------------------------------------------")
                    
                    return response.content.urls

            except Exception as e:
                if "429" in str(e):
                    if attempt < retries:
                        api = set_api(attempt, return_val = True)
                        continue
                else:
                    st.error(f"API quota exhausted for all keys. Please try later, {e}")
                    return None

    except Exception as e:
        st.error(f"Error: {e}")

def generate_timetable(report: str, syllabus: str, quiz_results = None, retries = len(API_KEYS)):
    api = set_api(0, return_val = True)
    for attempt in range(retries+1):
        try:
            tt = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                system_instruction="You are a very professional and experienced education developer. Provide a tabular timetable for 7 days (8-10 hours per day, in 1-hour periods) based on the provided report and syllabus."
            )
            pr_tt = f"""
        Generate the timetable for a student to completely cover the provided topics for each subject based on the student’s performance.
        Keep rows as days and columns as hours, and fill the timetable with the topics to be covered.
        Report:
        -----Start of the report--
        {report}
        ----End of the Report------
        Syllabus:
        -----Start of the Syllabus-----
        {syllabus}
        -----End of the Syllabus-----

        Note : Do not provide anything like, "Okay here is your response" or "Okay, based on" and something like that
        """
            
        
            if quiz_results:
                pr_tt += f""" The student wrote a quiz and this is the performance of the student, 
        Quiz Results: {quiz_results},
        Now based on the student's performance, generate the timetable for the student to cover the topics.
        """
            response = tt.generate_content(pr_tt)
            return response.text

        except Exception as e:
            if "429" in str(e):  
                if attempt < retries:
                    api = set_api(attempt, return_val = True)                        
                    continue
                else:
                    st.error(f"TT API quota exhausted for all keys. Please try later. {e}")
                    return None
            else:
                st.error(f"Unexpected error: {e}")
                return None

def generate_roadmap(report: str, syllabus: str, quiz_results = None, retries = len(API_KEYS)):
    api = set_api(0, return_val = True)
    mo = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                system_instruction="You are a very proficient educational roadmap generator. Provide a step-by-step roadmap for the student to excel based on the given report and syllabus. The roadmap should cover on how to start and go through the topics and chapters for each subject."
            )

    pr = f"""
    Generate the step-by-step roadmap for a student to ace his studies based on the provided report and syllabus.
    Report:
    -----Start of the report--
    {report}
    ----End of the Report------
    Syllabus:
    -----Start of the Syllabus-----
    {syllabus}
    -----End of the Syllabus-----

    Note : Do not provide anything like, "Okay here is your response" or "Okay, based on" and something like that
    """

    for attempt in range(retries+1):
        try:
            
            if quiz_results:
                    pr += f""" The student wrote a quiz and this is the performance of the student,
            Quiz Results: {quiz_results},
            Now based on the student's performance, generate the roadmap for the student to excel.
            """

            response = mo.generate_content(pr)
            return response.text

        except Exception as e:
            if "429" in str(e):  
                if attempt < retries:
                    api = set_api(attempt, return_val = True)  
                    continue

                else:
                    st.error(f"RMG - API quota exhausted for all keys. Please try later. {e}")
                    return None
            else:
                st.error(f"Unexpected error: {e}")
                return None                

class QuizModel(BaseModel):
    questions: List[str] = Field(..., description="The question for that topic of the given subject")
    answers: List[str] = Field(..., description="The correct option for the answer for that question")
    options: List[List[str]] = Field(..., description="The 4 options (a to d) for the particular question")
    expanation: List[str] = Field(..., description="The explanation for the answers")

def quiz_agent(api):
    quiz_model = Agent(
        model=Gemini(model='gemini-2.0-flash', api_key=api),
        tools=[DuckDuckGo(), SerpApiTools(api_key=sa)],
        instructions=[
            "Based on the given subject, report, and syllabus, generate a quiz consisting of 10 MCQs. Analyze the user's strengths and weaknesses from the report when designing questions."
        ],
        response_model=QuizModel,
        show_tool_calls=True
    )

    return quiz_model

def generate_quiz(report: str, syllabus: str, subject: str, retries = len(API_KEYS)):
    prompt_q = f"""
Generate the quiz for the {subject} subject, based on the given syllabus of the student.
-----Start of the Syllabus-----
{syllabus}
-----End of the Syllabus-----
And the report of the student is:
-----Start of the Report-----
{report}
-----End of the Report-----
"""
    try:
        api = set_api(0, return_val = True)
        for attempt in range(retries+1):
            try:
                quiz_model = quiz_agent(api)                
                response = quiz_model.run(prompt_q)
                return response.content

            except Exception as e:
                if "429" in str(e):
                    if attempt < retries:                        
                        api = set_api(attempt, return_val = True)                           
                        continue
                else:
                    st.error(f"API quota exhausted for all keys. Please try later. {e}")
                    return None

    except Exception as e:
        st.error(f"Error: {e}")

class Marks(BaseModel):
    marks: List[float] = Field(..., description="Marks obtained for each question")
    tot_mark: float = Field(..., description="Total marks for the quiz")

def marks_agent(api):
    mark_mod = Agent(
        model=Gemini(model='gemini-2.0-flash', api_key=api),
        instructions=[
        "Evaluate each question. Each correct answer earns 1 point, otherwise 0. Use the provided correct answers and user answers."
        ],
        response_model=Marks,
        show_tool_calls=True
    )

    return mark_mod

def correct_quiz(answers: List[str], user_answers: List[str], retries = len(API_KEYS)):
    prompt_mark = f"""
The correct answers:
{answers}

The user answers:
{user_answers}
"""
    try:
        api = set_api(0, return_val = True)
        for attempt in range(retries+1):
            try:
                mark_mod = marks_agent(api)                
                response = mark_mod.run(prompt_mark)
                return response.content

            except Exception as e:
                if "429" in str(e):
                    if attempt < retries:                        
                        api = set_api(attempt, return_val = True)                           
                        continue
                else:
                    st.error(f"API quota exhausted for all keys. Please try later. {e}")
                    return None

    except Exception as e:
        st.error(f"Error: {e}")

def analyze_report(report: str, retries = len(API_KEYS)):
    api = set_api(0, return_val = True)
    for attempt in range(retries+1):
        try:
            mod = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                system_instruction="You are a very professional academic report analyzer. Analyze the student's report and provide detailed strengths, weaknesses, and achievements."
            )
            prompt = f"Analyze the given student report:\n{report}\nNote : Do not provide anything like, 'Okay here is your response' or 'Okay, based on' and something like that"
            response = mod.generate_content(prompt)
            return response.text

        except Exception as e:
            if "429" in str(e):  
                if attempt < retries:
                    api = set_api(attempt, return_val = True)                        
                    continue

                else:
                    st.error(f"API quota exhausted for all keys. Please try later. {e}")
                    return None

            else:
                st.error(f"Unexpected error: {e}")
                return None        

def chatbot_response(user_message: str, syllabus: str = "", analysis_text: str = "", retries = len(API_KEYS)):
    api = set_api(0, return_val = True)
    for attempt in range(retries+1):
        try:
            mod = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                system_instruction="You are an educational assistant chatbot. Answer the user's question clearly and concisely, and in a deep manner based on the student analysis given, in simple language, but do not ignore technical words"
            )
            prompt = f"Answer the User question: {user_message}\n With respect to the Syllabus context: {syllabus} \n The Analysis of the student: {analysis_text}\nNote : Do not provide anything like, 'Okay here is your response' or 'Okay, based on' and something like that"
            response = mod.generate_content(prompt)
            return response.text

        except Exception as e:
            if "429" in str(e):  
                if attempt < retries:
                    api = set_api(attempt, return_val = True)                        
                    continue
                else:
                    st.error(f"API quota exhausted for all keys. Please try later. {e}")
                    return None
            else:
                st.error(f"Unexpected error: {e}")
                return None    

def chatbot_response_img(user_message: str, syllabus: str = "", img = None, analysis_text: str = "", retries = len(API_KEYS)):
    api = set_api(0, return_val = True)
    for attempt in range(retries+1):
        try:
            mod = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                system_instruction="You are an educational assistant chatbot. Answer the user's question clearly and concisely, and in a deep manner based on the student analysis given, in simple language, but do not ignore technical words"
            )
            response = mod.generate_content(["Answer the Question from the given image with respect to the syllabus of the student, while answering certain questions you can also use the knowledge from outside the image too (but just verify whether it is related to the image)\n"
                                    f"Syllabus: {syllabus}\n"
                                    f"Question: {prompt}\n",
                                    f"Analysis Text : {analysis_text}\n",
                                    img
                                ])
            return response.text

        except Exception as e:
            if "429" in str(e):  
                if attempt < retries:
                    api = set_api(attempt, return_val = True)                        
                    continue
                else:
                    st.error(f"API quota exhausted for all keys. Please try later. {e}")
                    return None
            else:
                st.error(f"Unexpected error: {e}")
                return None    

def chatbot_response_vid(user_message: str, syllabus: str = "", context: str = "", analysis_text: str = "", retries = len(API_KEYS)):
    api = set_api(0, return_val = True)
    for attempt in range(retries+1):
        try:
            mod = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                system_instruction="You are an educational assistant chatbot. Answer the user's question clearly and concisely, and in a deep manner based on the student analysis given, in simple language, but do not ignore technical words"
            )

            response = mod.generate_content("Answer the Question from the given Context with respect to the syllabus provided and the given student analysis\n"
                                    f"Syllabus: {syllabus}\n"
                                    f"Question: {prompt}\n"
                                    f"Context: {context}\n"
                                    f"Analysis Text : {analysis_text}\n"
                                )
            
            return response.text

        except Exception as e:
            if "429" in str(e):  
                if attempt < retries:
                    api = set_api(attempt, return_val = True)                        
                    continue
                else:
                    st.error(f"API quota exhausted for all keys. Please try later. {e}")
                    return None
            else:
                st.error(f"Unexpected error: {e}")
                return None    
        
def parse_gemini_response(response_text):
    try:
        cleaned = re.sub(r'```json|```', '', response_text)
        json_str = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_str:
            return json.loads(json_str.group())
        return None

    except Exception as e:
        st.error(f"Failed to parse response: {str(e)}")
        return None

def extract_topic(question : str = '', retries = len(API_KEYS)):
    api = set_api(0, return_val = True)
    for attempt in range(retries+1):
        try:
            extract_mod = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction = "You are a very professional and highly talented educational assistant. Extract the topics which are related to the question."
        )

            prompt = f"""
            Extract the topic for which the provided questions is related to.
            Question : {question},
            The output should be in a STRICT JSON format.

            Topic : string

            Note : Do not provide anything like, "Okay here is your response" or "Okay, based on" and something like that
            """
            response = extract_mod.generate_content(prompt)
            return parse_gemini_response(response.text)

        except Exception as e:
            if "429" in str(e):  
                if attempt < retries:
                    api = set_api(attempt, return_val = True)                        
                    continue
                else:
                    st.error(f"API quota exhausted for all keys. Please try later. {e}")
                    return None
            else:
                st.error(f"Unexpected error: {e}")
                return None    

def get_from_uploads(image_file):
    file_path = get_local_path(image_file.name)
    with open(file_path, "wb") as f:
        while chunk := image_file.read(1024 * 1024):  
            f.write(chunk)
    return file_path 

@st.cache_data
def load_img(img_url):
    filename = os.path.basename(img_url).split("?")[0]
    response = requests.head(img_url)
    content_type = response.headers.get('content-type', '')
    extension = content_type.split("/")[-1]
    if extension not in ['jpeg', 'png', 'gif', 'bmp', 'webp']:
        extension = 'jpg'

    file_path = get_local_path(f"{filename.split('.')[0]}.{extension}")

    if 'image' not in content_type:
        raise ValueError("URL does not point to an image")

    img_resp = requests.get(img_url, stream=True)
    img_resp.raise_for_status()

    with open(file_path, 'wb') as f:
            f.write(img_resp.content)

    return file_path

def get_local_path(filename):
    safe_filename = os.path.basename(filename).replace(" ", "_")
    downloads_folder = os.path.join("downloads")
    os.makedirs(downloads_folder, exist_ok=True)    
    return os.path.join(downloads_folder, safe_filename)

def extract_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        if parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
        if parsed.path.startswith('/v/'):
            return parsed.path.split('/')[2]
    return None

def read_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def transcribe_video(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # transcript = transcript_list.find_transcript(['en'])
        # translated = transcript.translate('en').fetch()
        return {
            # 'translated': ' '.join([i['text'] for i in translated]),
            'original': ' '.join([i['text'] for i in transcript]),
            'language': 'en'
        }

    except:
        # try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # transcript = transcript_list.find_transcript(['en'])
        # translated = transcript.translate('en').fetch()
        return {
            # 'translated': ' '.join([i['text'] for i in translated]),
            'original': ' '.join([i['text'] for i in transcript]),
            'language': 'en'
        }

        # except Exception as e:
        #     st.error(f"Transcript error: {str(e)}")
        #     return None



st.set_page_config(page_title="Student Analyzer AI", layout="wide", page_icon = ":book")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "current_group" not in st.session_state:
    st.session_state.current_group = None
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "quiz_in_progress" not in st.session_state:
    st.session_state.quiz_in_progress = False
if "subjects" not in st.session_state:
    st.session_state.subjects = []
if 'edu_level' not in st.session_state:
    st.session_state.edu_level = None
if 'report' not in st.session_state:
    st.session_state.report = ""
if 'current_img' not in st.session_state:
    st.session_state.current_img = {'img_id' : None, 'path' : None,'image' : None}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}
if 'current_video' not in st.session_state:
    st.session_state.current_video = {'id': None}
if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'username' not in st.session_state:
    st.session_state.username = None

st.title("Student Analyzer AI")

if not st.session_state.logged_in: 

    st.subheader("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        user_id = login_user(username, password)
        if user_id:
            st.session_state.logged_in = True
            st.session_state.user_id = user_id
            st.session_state.username = username
            st.success("Logged in successfully!")
            log_action(user_id, None, "login", "User logged in")
            st.rerun()
        else:
            st.error("Invalid credentials")

else :
    st.sidebar.header(f"Welcome back !! {st.session_state.username}")
    with st.sidebar:
        if st.sidebar.checkbox("Change Password", key="change_pw_checkbox"):
            new_pw = st.sidebar.text_input("New Password", type="password", key="new_pw")
            confirm_pw = st.sidebar.text_input("Confirm New Password", type="password", key="confirm_pw")
            if st.sidebar.button("Update Password", key="update_pw_button"):
                if new_pw and new_pw == confirm_pw:
                    change_password(st.session_state.user_id, new_pw)
                    st.success("Password updated!")
                else:
                    st.error("Passwords do not match or are empty.")
        if st.session_state.current_group:
            st.sidebar.success(f"Current Group ID for analysis: {st.session_state.current_group}")
            
        st.write("### File Upload & Grouping")
        file_continuation = st.radio("Is this file a continuation of an existing group?", ("No", "Yes"), key="file_continuation")
        if file_continuation == "No":
            new_group_name = st.text_input("Enter a new group name for these files", key="new_group")
        else:
            groups = get_user_groups(st.session_state.user_id)
            if groups:
                group_options = {str(g[0]): g[1] for g in groups}
                selected_group = st.selectbox("Select an existing group", options=list(group_options.keys()),
                                            format_func=lambda x: group_options[x], key="select_group")
                new_group_name = group_options[selected_group]
                st.session_state.current_group = int(selected_group)
            else:
                st.warning("No existing groups found. Please create a new group.")
                new_group_name = st.text_input("Enter a new group name for these files", key="new_group2")

        uploaded_file = st.file_uploader("Upload Report File(s)", accept_multiple_files=False, key="report_files", type =["txt","pdf"])
        if st.button("Upload Files"):
            if uploaded_file:
                if file_continuation == "No":
                    group_id = create_file_group(st.session_state.user_id, new_group_name)
                    st.session_state.current_group = group_id

                else:
                    group_id = st.session_state.current_group
                                    
                if uploaded_file.type == "text/plain":
                    file_content = uploaded_file.getvalue().decode("utf-8")

                elif uploaded_file.type == "application/pdf":
                    file_content = read_pdf(uploaded_file)                    

                save_file(group_id, uploaded_file.name, uploaded_file.type, file_content)
                st.success(f"Uploaded {uploaded_file.name}")
                log_action(st.session_state.user_id, group_id, "upload_file", f"Uploaded file: {uploaded_file.name}")

                st.rerun()

            else:
                st.error("No files selected.")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.current_group = None
            st.rerun()

if st.session_state.current_group:
    c = conn.cursor()
    c.execute("SELECT file_content FROM files WHERE group_id=?", (st.session_state.current_group,))
    files_data = c.fetchall()
    report = ""
    for file_data in files_data:
        try:
            report += file_data[0].decode("utf-8") + "\n"
        except Exception:
            report += str(file_data[0]) + "\n"
        
    st.session_state.report = report

if st.session_state.logged_in:    
    tabs = st.tabs(["Dashboard", "Syllabus", "Recommendation", "Quiz", "Chatbot", "Uploaded Files", "Performance"])
    
    with tabs[0]:
        st.header("Dashboard")
        if st.session_state.current_group is None:
            st.warning("No file group selected. Please upload files or select a file group from 'Uploaded Files' tab.")
        else:
            analysis_data = get_latest_analysis(st.session_state.current_group)
            if analysis_data:
                analysis_text, timetable_text, roadmap_text, ts = analysis_data
                st.session_state.analysis_text = analysis_text
                st.subheader("Latest Analysis Report")
                st.markdown(analysis_text)
                st.markdown("---")
                st.subheader("Latest Timetable")
                st.markdown(timetable_text)
                st.markdown("---")
                st.subheader("Latest Roadmap")
                st.markdown(roadmap_text)
                st.markdown("---")
                st.caption(f"Generated on: {ts}")
            else:
                st.info("No analysis performed yet. Please go to the 'Recommendation' tab and perform analysis.")
    
    with tabs[1]:
        st.header("Syllabus Generator")     
        course_id = get_user_details_course(st.session_state.user_id)[0]
        syllabus_content = get_syllabus_for_course(course_id)[0]
        
        if syllabus_content:
            st.write("Rate your understanding for each topic (Scale of 1 to 10):")
            topic_ratings = {}
            topics_list = [t.strip() for t in syllabus_content.split("\n") if t.strip()]
            for topic in topics_list:
                st.markdown(f"- **{topic}**")
                topic_ratings[topic] = st.slider(f"Rating for -> {topic}", 1, 10, 5, key=f"rate_{topic}")
        else:
            topic_ratings = {}

        if st.button("Save Syllabus"):
            if st.session_state.current_group is None:
                st.error("Please upload report files first to create/select a group.")

            elif not syllabus_content:
                st.error("Syllabus content cannot be empty.")

            else:
                save_syllabus(st.session_state.current_group, syllabus_content, topic_ratings)
                st.success(f"Syllabus saved successfully!, for group id {st.session_state.current_group}")
                log_action(st.session_state.user_id, st.session_state.current_group, "save_syllabus", "Syllabus saved")
                st.session_state.analysis_done = False                
    
    with tabs[2]:
        st.header("Recommendations")
        if st.session_state.current_group is None:
            st.warning("No file group selected.")
        else:
            c = conn.cursor()
            c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (st.session_state.current_group,))
            row = c.fetchone()

            syllabus = row[0] if row else ""

            if not report and not syllabus:
                st.error("Both report and syllabus are required for analysis.")            

            else:
                if st.button("Perform Analysis & Generate Recommendations"):
                    user_details = get_user_details(st.session_state.user_id)
                    st.session_state.edu_level = user_details[1] if user_details else "Unknown"
                    edu_level = st.session_state.edu_level

                    with st.spinner("Generating analysis..."):
                        analysis_text = analyze_report(report, retries)
                    st.success("Analysis completed!")                                       

                    with st.spinner("Generating timetable"):
                        timetable_text = generate_timetable(report, syllabus, retries)
                    st.success("Timetable generated!")

                    with st.spinner("Generating roadmap"):
                        roadmap_text = generate_roadmap(report, syllabus, retries)
                    st.success("Roadmap generated!")
                
                    save_analysis_result(st.session_state.current_group, analysis_text, timetable_text, roadmap_text)
                    log_action(st.session_state.user_id, st.session_state.current_group, "perform_analysis", "Analysis performed")
                    st.success("Analysis and recommendations generated!")
                    st.session_state.analysis_done = True
                    st.rerun()

                analysis_data = get_latest_analysis(st.session_state.current_group)
                if analysis_data:
                    selection = st.selectbox("Select Recommendation", ["Analysis Report", "Timetable", "Roadmap", "Sources"])
                    analysis_text, timetable_text, roadmap_text, _ = analysis_data
                    if selection == "Analysis Report":
                        st.subheader("Analysis Report")
                        st.markdown(analysis_text)
                    elif selection == "Timetable":
                        st.subheader("Timetable")
                        st.markdown(timetable_text)
                    elif selection == "Roadmap":
                        st.subheader("Roadmap")
                        st.markdown(roadmap_text)
                    else:
                        st.subheader("Sources")
                        st.write("### YouTube Videos")

                        for i in syllabus.split("\n"):                            
                            st.markdown('----')
                            st.subheader(i)
                            if st.button(f"Generate Youtube Recommendations for {i}"):

                                with st.spinner(f"Fetching videos for {i}..."):
                                    yt_video_ids = youtube_video_recommendation(f"{i} educational course videos, for {st.session_state.edu_level} students")

                                st.subheader(f"Videos for {i}")
                                rows = st.columns(2)

                                for video_id in yt_video_ids:
                                    with rows[0]:
                                        st.write(f"**{video_id['title']}**")                                    
                                        st.write(f"URL: [Watch Video](https://www.youtube.com/watch?v={video_id['id']})")
                                    
                                    with rows[0]:
                                        st.video(f"https://www.youtube.com/watch?v={video_id['id']}")
                                    
                                        st.markdown('---')

                            if st.button(f"Generate Website Recommendations for {i}"):
                                st.write("### Related Websites")
                                with st.spinner(f"Fetching related websites for {i}..."):
                                    websites = fetch_related_websites(f"{i} educational websites , for {st.session_state.edu_level} students", retries)
                                if websites:
                                    st.write(f"Websites for {i}")
                                    for site in websites:
                                        st.markdown(f"[{site}]({site})")
                                    st.markdown('---')
                        
    with tabs[3]:
        st.header("Quiz")

        if st.session_state.current_group is None:
            st.warning("No file group selected.")
        else:
            c = conn.cursor()
            c.execute("SELECT file_content FROM files WHERE group_id=?", (st.session_state.current_group,))
            files_data = c.fetchall()
            report = ""

            for file_data in files_data:
                try:
                    report += file_data[0].decode("utf-8") + "\n"
                except Exception:
                    report += str(file_data[0]) + "\n"

            c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (st.session_state.current_group,))
            row = c.fetchone()
            syllabus = row[0] if row else ""
            
            if not report and not syllabus:
                st.error("Both report and syllabus are required to generate a quiz.")

            else:
                subjects_extracted = syllabus.split("\n")
                if subjects_extracted:
                    st.write("Extracted Subjects:")
                    selected_subject = st.selectbox("Select a subject for the quiz", options=subjects_extracted)
                    if st.button("Generate Quiz for " + selected_subject):
                        with st.spinner("Generating quiz..."):
                            quiz_content = generate_quiz(report, syllabus, selected_subject, retries)

                        st.session_state.quiz_in_progress = True
                        st.session_state.current_quiz = {
                            "subject": selected_subject,
                            "questions": quiz_content.questions,
                            "options": quiz_content.options,
                            "answers": quiz_content.answers,
                            "explanations": quiz_content.expanation
                        }
                        st.session_state.resources = {
                            "Google" :  [],
                            "YouTube" : []
                        }
                else:
                    st.error("No subjects could be extracted from the report.")
                                
                if st.session_state.quiz_in_progress:
                    st.subheader(f"Quiz: {st.session_state.current_quiz['subject']}")
                    user_answers = []
                    for i, question in enumerate(st.session_state.current_quiz["questions"], start=1):
                        st.markdown(f"**Q{i}: {question}**")
                        options = st.session_state.current_quiz["options"][i-1]
                        answer = st.radio(f"Select answer for Q{i}", options, key=f"quiz_q_{i}")
                        user_answers.append(answer)

                    if st.button("Submit Quiz"):
                        with st.spinner("Evaluating quiz..."):
                            correction = correct_quiz(st.session_state.current_quiz["answers"], user_answers, retries)

                        marks = correction.marks
                        tot_marks = correction.tot_mark
                        st.success(f"You scored {tot_marks} out of {len(st.session_state.current_quiz['questions'])}")
                        
                        with st.expander("View Detailed Explanations and Your Answers"):
                            for i, question in enumerate(st.session_state.current_quiz["questions"], start=1):
                                try:                                
                                    st.markdown(f"**Q{i}: {question}**")
                                    st.write(f"Your answer: {user_answers[i-1]}")
                                    st.write(f"Correct answer: {st.session_state.current_quiz['answers'][i-1]}")
                                    st.write(f"Explanation: {st.session_state.current_quiz['explanations'][i-1]}")
                                    st.session_state.resources["Google"].append(f"https://www.google.com/search?q={extract_topic(question, retries)['Topic'].replace(' ','+')}")
                                    st.session_state.resources["YouTube"].append(f"https://www.youtube.com/results?search_query={extract_topic(question, retries)['Topic'].replace(' ','+')})")
                                    st.write(f"Related Content Search: [Search on Google]({st.session_state.resources["Google"][i-1]})")
                                    st.write(f"Related YouTube videos : [Search on YouTube]({st.session_state.resources["YouTube"][i-1]})")
                                    st.markdown("---")

                                except Exception as e:                                       
                                    st.markdown(f"**Q{i}: {question}**")
                                    st.write(f"Your answer: {user_answers[i-1]}")
                                    st.write(f"Correct answer: {st.session_state.current_quiz['answers'][i-1]}")
                                    st.write(f"Explanation: {st.session_state.current_quiz['explanations'][i-1]}")
                                    st.session_state.resources["Google"].append(f"https://www.google.com/search?q={question.replace(' ','+')}")
                                    st.session_state.resources["YouTube"].append(f"https://www.youtube.com/results?search_query={question.replace(' ','+')})")
                                    st.write(f"Related Content Search: [Search on Google]({st.session_state.resources["Google"][i-1]})")
                                    st.write(f"Related YouTube videos : [Search on YouTube]({st.session_state.resources["YouTube"][i-1]})")
                                    st.markdown("---")

                                                   
                        quiz_details = {
                            "subject": st.session_state.current_quiz["subject"],
                            "questions": st.session_state.current_quiz["questions"],
                            "options": st.session_state.current_quiz["options"],
                            "correct_answers": st.session_state.current_quiz["answers"],
                            "user_answers": user_answers,
                            "marks": marks,
                            "explanations": st.session_state.current_quiz["explanations"],
                            "related_content": st.session_state.resources["Google"],
                            "related_videos": st.session_state.resources["YouTube"]
                        }
                        
                        with st.spinner("Saving the Quiz information"):
                            save_quiz_result(st.session_state.user_id, st.session_state.current_group, st.session_state.current_quiz["subject"], tot_marks, quiz_details)
                            log_action(st.session_state.user_id, st.session_state.current_group, "quiz", f"Quiz taken on subject {st.session_state.current_quiz['subject']} with score {tot_marks}")
                            st.session_state.quiz_in_progress = False

                        with st.spinner("Updating Timetable and Roadmap..."):
                            try:
                                timetable_text = generate_timetable(report, syllabus, quiz_results=quiz_details, retries = retries)
                                roadmap_text = generate_roadmap(report, syllabus, quiz_results=quiz_details, retries = retries)
                                save_analysis_result(st.session_state.current_group, analysis_text, timetable_text, roadmap_text)
                                st.success("Timetable and Roadmap updated successfully!")
                                log_action(st.session_state.user_id, st.session_state.current_group, "update_analysis", "Timetable and Roadmap updated")

                            except Exception as e:
                                st.error(f"Failed to update timetable and roadmap at this point of time: {str(e)}")
    
    with tabs[4]:
        st.header("Educational Assistant Chat")
        st.info("Ask your questions here. For image and video related chat change the models.")

        if st.session_state.current_group is None:
            st.warning("No file group selected.")
        
        else:
            c = conn.cursor()
            c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (st.session_state.current_group,))
            row = c.fetchone()

            syllabus = row[0] if row else ""

            chat_mod = st.selectbox("Select Chat Mode", ["Text Chat", "Image Chat", "YouTube Video Chat"], key="chat_mode")
            
            if chat_mod == "Image Chat":
                st.header("Educational Assistant Chat - Image")
                st.info("Ask your questions about the image here.")

                if st.session_state.current_group is None:
                    st.warning("No file group selected.")
                else:
                    c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (st.session_state.current_group,))
                    row = c.fetchone()
                    syllabus = row[0] if row else ""

                    st.subheader("Image Chat Assistant")

                    with st.expander("Previous Images"):
                        c.execute("SELECT DISTINCT image_id, image_path FROM chat_history_image WHERE user_id=? AND group_id=?",
                                (st.session_state.user_id, st.session_state.current_group))
                        previous_images = c.fetchall()
                        for img_rec in previous_images:
                            prev_img_id, prev_img_path = img_rec
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                try:
                                    prev_img = Image.open(prev_img_path)
                                    st.image(prev_img, width=100)
                                except Exception:
                                    st.write("Image load error")
                            with col2:
                                if st.button("Load this", key=f"load_{prev_img_id}"):
                                    st.session_state.current_img['path'] = prev_img_path
                                    try:
                                        st.session_state.current_img['image'] = Image.open(prev_img_path)
                                    except Exception:
                                        st.session_state.current_img['image'] = None
                                    st.session_state.current_img['img_id'] = prev_img_id                                    
                                    st.success("Image loaded!")

                    chat_mod_option = st.selectbox("Choose way of uploading an image", 
                                                ["Upload the file", "Paste the link of the Image"])
                    rows = st.columns(2)
                    if chat_mod_option == "Upload the file":
                        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"], key="img_upload")
                        if uploaded_file:
                            try:
                                file_path = get_from_uploads(uploaded_file)
                                st.session_state.current_img['path'] = file_path
                                st.session_state.current_img['image'] = Image.open(file_path)
                                with rows[1]:
                                    st.image(st.session_state.current_img['image'], caption='Uploaded Image', use_container_width=True)
                            except Exception as e:
                                st.error(f"Failed to upload image: {str(e)}")

                    else:
                        img_url = st.text_input("Paste the link of the image file", help="Paste the image link", key="img_url")
                        if img_url:
                            try:
                                file_path = load_img(img_url)
                                st.session_state.current_img['path'] = file_path
                                st.session_state.current_img['image'] = Image.open(file_path)
                                with rows[1]:
                                    st.image(st.session_state.current_img['image'], caption='Loaded Image', use_container_width=True)
                            except Exception as e:
                                st.error(f"Failed to download image: {str(e)}")

                    if st.session_state.current_img['path']:
                        st.image(st.session_state.current_img['image'], width = 300)
                        img_id = st.session_state.current_img['path']
                        if st.session_state.current_img.get('img_id') != img_id:
                            st.session_state.current_img['img_id'] = img_id
                            st.session_state.chat_history[img_id] = []

                    current_img_id = st.session_state.current_img.get('img_id')
                    if current_img_id:
                        chat_history_img = get_chat_history_image(st.session_state.user_id, st.session_state.current_group, current_img_id)
                        for role, message in chat_history_img:
                            with st.chat_message(role):
                                st.markdown(message)
                        
                        prompt = st.chat_input("Ask about the image", key="img_chat_input")
                        if prompt:
                            with st.spinner("Thinking..."):
                                try:
                                    response = chatbot_response_img(prompt, syllabus, st.session_state.current_img['image'], st.session_state.analysis_text, retries)
                                except Exception as e:
                                    st.error(f"Failed to generate response: {str(e)}")
                                    response = "I am sorry, I could not generate a response at this time."
                            with st.chat_message("user"):
                                st.markdown(prompt)
                            with st.chat_message("assistant"):
                                st.markdown(response)
                            save_chat_message_image(st.session_state.user_id, st.session_state.current_group, current_img_id,
                                                    st.session_state.current_img['path'], "user", prompt)
                            save_chat_message_image(st.session_state.user_id, st.session_state.current_group, current_img_id,
                                                    st.session_state.current_img['path'], "assistant", response)
                            log_action(st.session_state.user_id, st.session_state.current_group, "image_chat", f"User: {prompt} | Assistant: {response}")

            elif chat_mod == "Text Chat":
                st.subheader("Text Chat Assistant")
                chat_history = get_chat_history(st.session_state.user_id, st.session_state.current_group)

                for role, message in chat_history:
                    if role == "user":
                        st.chat_message("user").markdown(message)
                    else:
                        st.chat_message("assistant").markdown(message)

                user_message = st.chat_input("Type your message here")

                if user_message:
                    with st.spinner("Generating response..."):
                        try:
                            response = chatbot_response(user_message, syllabus, st.session_state.analysis_text, retries)
                        except Exception as e:
                            st.error(f"Failed to generate response: {str(e)}")
                            response = "I am sorry, I could not generate a response at this time."

                    st.chat_message("user").markdown(user_message)
                    st.chat_message("assistant").markdown(response)

                    save_chat_message(st.session_state.user_id, st.session_state.current_group, "user", user_message)
                    save_chat_message(st.session_state.user_id, st.session_state.current_group, "assistant", response)
                    log_action(st.session_state.user_id, st.session_state.current_group, "chat", f"User: {user_message} | Assistant: {response}")

            elif chat_mod == "YouTube Video Chat":
                st.header("Educational Assistant Chat - YouTube Video")
                st.info("Ask your questions about the YouTube video here.")

                if st.session_state.current_group is None:
                    st.warning("No file group selected.")
                else:
                    c.execute("SELECT syllabus_content FROM syllabus_for_students WHERE group_id=?", (st.session_state.current_group,))
                    row = c.fetchone()
                    syllabus = row[0] if row else ""

                    st.subheader("YouTube Video Chat Assistant")

                    with st.expander("Previous Videos"):
                        c.execute("SELECT DISTINCT video_id, video_url FROM chat_history_video WHERE user_id=? AND group_id=?",
                                (st.session_state.user_id, st.session_state.current_group))
                        previous_videos = c.fetchall()
                        for vid_rec in previous_videos:
                            prev_video_id, prev_video_url = vid_rec
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.write(f"Video Name: {get_youtube_video_title(prev_video_url)}")
                                
                            with col2:
                                if st.button("Load this", key=f"load_video_{prev_video_id}"):
                                    st.session_state.current_video['id'] = prev_video_id
                                    st.session_state.current_video['video_url'] = prev_video_url
                                    st.success("Video loaded!")

                    video_url = st.text_input("Enter YouTube URL:", help="Paste a YouTube video URL here", key="video_url_input")
                    if video_url:
                        video_id = extract_video_id(video_url)
                        st.session_state.current_video['id'] = video_id
                        st.session_state.current_video['video_url'] = video_url

                    rows = st.columns(2)
                    if st.button("Process Video"):
                        with st.spinner("Analyzing video..."):
                            st.session_state.transcript = transcribe_video(st.session_state.current_video['id'])

                    with rows[1]:
                        if st.session_state.current_video.get('id'):
                            st.components.v1.html(
                                f"""<iframe width="100%" height="200" 
                                src="https://www.youtube.com/embed/{st.session_state.current_video['id']}?controls=1" 
                                frameborder="0" allowfullscreen></iframe>""",
                                height=200,
                                width=400,
                            )

                    current_video_id = st.session_state.current_video.get('id')
                    if current_video_id:
                        chat_history_vid = get_chat_history_video(st.session_state.user_id, st.session_state.current_group, current_video_id)
                        for role, message in chat_history_vid:
                            with st.chat_message(role):
                                st.markdown(message)
                        
                        prompt = st.chat_input("Ask about the video", key="video_chat_input")
                        if prompt:
                            with st.spinner("Thinking..."):
                                try:
                                    context = st.session_state.transcript.get('original', '')
                                    response = chatbot_response_vid(prompt, syllabus, context, st.session_state.analysis_text, retries)
                                except Exception as e:
                                    st.error(f"Failed to generate response: {str(e)}")
                                    response = "I am sorry, I could not generate a response at this time."
                            with st.chat_message("user"):
                                st.markdown(prompt)
                            with st.chat_message("assistant"):
                                st.markdown(response)
                            save_chat_message_video(st.session_state.user_id, st.session_state.current_group, current_video_id,
                                                    st.session_state.current_video['video_url'], "user", prompt)
                            save_chat_message_video(st.session_state.user_id, st.session_state.current_group, current_video_id,
                                                    st.session_state.current_video['video_url'], "assistant", response)
                            log_action(st.session_state.user_id, st.session_state.current_group, "video_chat", f"User: {prompt} | Assistant: {response}")
    
    with tabs[5]:
        st.header("Uploaded Files")
        groups = get_user_groups(st.session_state.user_id)
        if groups:
            for group_id, group_name in groups:
                st.subheader(f"Group: {group_name} (ID: {group_id})")
                if st.button(f"Select Group '{group_name}' for Analysis", key=f"select_group_{group_id}"):
                    st.session_state.current_group = group_id
                    st.success(f"Selected group '{group_name}' for analysis")
                    st.session_state.current_img['path'] = None
                    st.session_state.current_img['image'] = None
                    st.session_state.current_video['id'] = None
                    st.session_state.current_video['url'] = None
                    st.rerun()

                c = conn.cursor()
                c.execute("SELECT id, file_name, uploaded_at FROM files WHERE group_id=?", (group_id,))
                files = c.fetchall()

                if files:
                    for fid, fname, fut in files:
                        with st.expander(f"{fname} - Uploaded at {fut}"):
                            c.execute("SELECT file_content FROM files WHERE id=?", (fid,))
                            file_content = c.fetchone()[0]

                            if st.button("Delete File", key = f"{fname}_{fid}_del"):
                                delete_file(fid)
                                st.success(f"File '{fname}' deleted")
                                st.rerun()
                            try:
                                st.text(file_content.decode("utf-8"))
                            except Exception:
                                st.write(file_content)
                else:
                    st.write("No files in this group.")
        else:
            st.info("No file groups found.")
    

    with tabs[6]:
        st.header("Performance Overview")
        if st.session_state.current_group is None:
            st.warning("No file group selected.")
        else:
            quiz_results = get_quiz_results(st.session_state.user_id, st.session_state.current_group)
            if quiz_results:
                df = pd.DataFrame(quiz_results, columns=["Subject", "Quiz Date", "Total Marks", "Details"])
                df["Quiz Date"] = pd.to_datetime(df["Quiz Date"])
                df["Total Marks"] = pd.to_numeric(df["Total Marks"])
                st.line_chart(df.set_index("Quiz Date")["Total Marks"])
                st.subheader("Past Quiz Results")
                for index, row in df.iterrows():
                    with st.expander(f"{row['Subject']} quiz on {row['Quiz Date'].strftime('%Y-%m-%d %H:%M:%S')} - Score: {row['Total Marks']}"):
                        content = json.loads(row['Details'])
                        for i in range(len(content["questions"])):
                            st.write(f"**Q{i+1}: {content['questions'][i]}**")
                            st.write(f"Your Answer: {content['user_answers'][i]}")
                            st.write(f"Correct Answer: {content['correct_answers'][i]}")
                            st.write(f"Explanation: {content['explanations'][i]}")
                            st.write(f"Marks: {content['marks'][i]}")
                            if 'related_content' in content:
                                st.write(f"Related Content: [Search on Google]({content['related_content'][i]})") 
                                st.write(f"Related Videos: [Search on YouTube]({content['related_videos'][i]})") 
                            st.markdown("---")
            else:
                st.info("No quiz results found.")

else:
    st.sidebar.info("Please log in to continue.")