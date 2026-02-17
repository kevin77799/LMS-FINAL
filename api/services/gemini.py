import json
import re
from typing import Any, Dict, List, Optional
from functools import wraps

# --- Centralized Configuration ---
GEMINI_MODEL = "gemini-2.0-flash"

# --- Conditional Imports ---
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
except ImportError:
    genai = None

try:
    from phi.agent import Agent
    from phi.tools.duckduckgo import DuckDuckGo
    from phi.tools.serpapi_tools import SerpApiTools
    from phi.model.google import Gemini
except ImportError:
    Agent = None
    Gemini = None

from ..core.config import API_KEYS, SERP_API_KEY


# --- Decorator for Retry and API Key Rotation Logic (Corrected Version) ---
def with_gemini_retry(func=None, *, default_return="[Gemini not installed]"):
    """
    A decorator that handles Gemini API calls with retries and API key rotation.
    It can be used as @with_gemini_retry or @with_gemini_retry(default_return=...)
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not genai:
                return default_return

            retries = kwargs.get('retries', 3)

            for attempt in range(min(retries, len(API_KEYS))):
                try:
                    api_key = API_KEYS[attempt]
                    genai.configure(api_key=api_key)
                    return f(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    # Retry on rate limit (429) or invalid key (400/expired)
                    if ("429" in error_str or "400" in error_str or "API key expired" in error_str) and attempt < len(API_KEYS) - 1:
                        print(f"API key {attempt} failed: {error_str}. Trying next key.")
                        continue
                    
                    print(f"An unrecoverable error occurred: {e}")
                    if attempt == min(retries, len(API_KEYS)) - 1:
                        break # Exit loop to fall through to default return
                    raise
            
            return default_return
        return wrapper

    if func:
        return decorator(func)
    return decorator

@with_gemini_retry
def analyze_report(report: str, **kwargs) -> str:
    mod = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=(
            "You are a very professional academic report analyzer. "
            "Analyze the student's report and provide detailed strengths, weaknesses, and achievements."
        ),
    )
    prompt = f"Analyze the given student report:\n{report}\n\nNote: Do not include prefatory phrases; answer directly."
    resp = mod.generate_content(prompt)
    return getattr(resp, "text", "")

@with_gemini_retry
def generate_timetable(report: str, syllabus: str, quiz_results: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    mod = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=(
            "You are a professional education developer. Provide a tabular timetable for 7 days "
            "(8-10 hours per day in 1-hour periods) based on the provided report and syllabus."
        ),
    )
    prompt = f"Generate a weekly timetable to cover the provided topics for each subject based on the student's performance.\nReport:\n{report}\nSyllabus:\n{syllabus}"
    if quiz_results:
        prompt += f"\nQuiz Results Context: {json.dumps(quiz_results)[:3000]}"
    resp = mod.generate_content(prompt)
    return getattr(resp, "text", "")

@with_gemini_retry
def generate_roadmap(report: str, syllabus: str, quiz_results: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    mod = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=(
            "You are a proficient educational roadmap generator. Provide a step-by-step roadmap for the student "
            "to excel based on the given report and syllabus."
        ),
    )
    prompt = f"Generate a step-by-step roadmap from the report and syllabus.\nReport:\n{report}\nSyllabus:\n{syllabus}"
    if quiz_results:
        prompt += f"\nQuiz Results Context: {json.dumps(quiz_results)[:3000]}"
    resp = mod.generate_content(prompt)
    return getattr(resp, "text", "")

@with_gemini_retry
def extract_topic(question: str, **kwargs) -> Optional[str]:
    mod = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction="You are an educational assistant. Extract the concise topic that the question relates to.",
    )
    prompt = f"Question: {question}\nReturn only the topic phrase."
    resp = mod.generate_content(prompt)
    text = getattr(resp, "text", "").strip()
    return text.split("\n")[0] if text else None

def generate_quiz_json(report: str, syllabus: str, subject: str) -> Dict[str, Any]:
    # Try phi Agent + tools first
    if Agent and Gemini and SERP_API_KEY:
        try:
            genai.configure(api_key=API_KEYS[0])
            quiz_agent = Agent(
                model=Gemini(model=GEMINI_MODEL),
                tools=[DuckDuckGo(), SerpApiTools(api_key=SERP_API_KEY)],
                instructions=[
                    "Based on the given subject, report, and syllabus, generate a quiz of 10 MCQs. "
                    "Analyze weaknesses from the report when designing questions. "
                    "Return a valid JSON object with keys: 'questions', 'options', 'answers', and 'explanations'."
                ],
                json_output=True,
            )
            prompt = f"Generate the quiz for {subject} based on the syllabus and report.\nSyllabus:\n{syllabus}\nReport:\n{report}"
            response_json = quiz_agent.run(prompt)
            if isinstance(response_json, dict):
                return response_json
        except Exception as e:
            print(f"Phi-agent quiz generation failed: {e}. Falling back to standard Gemini.")

    # Fallback to Gemini only with enforced JSON mode
    if not genai:
        return {}

    @with_gemini_retry(default_return={})
    def generate_with_fallback(**kwargs):
        json_generation_config = GenerationConfig(response_mime_type="application/json")
        mod = genai.GenerativeModel(
            model_name=GEMINI_MODEL, 
            generation_config=json_generation_config
        )
        prompt = f"""
        Create 10 Multiple Choice Questions for the subject '{subject}' using the provided syllabus and student report.
        Focus on areas of weakness identified in the report.

        Return a valid JSON object. The root object must have these four keys and only these four keys: 
        1. "questions": A list of 10 question strings.
        2. "options": A list of 10 lists, where each inner list contains 4 option strings.
        3. "answers": A list of 10 correct answer strings.
        4. "explanations": A list of 10 strings. EACH question MUST have a concise explanation for why the correct answer is right. This field is mandatory.

        Syllabus:
        {syllabus}
        Report:
        {report}
        """
        # --- END OF REPLACEMENT ---

        resp = mod.generate_content(prompt)
        return json.loads(resp.text)

    # Call the now-decorated function
    return generate_with_fallback()
