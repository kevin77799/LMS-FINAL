import os
from typing import List, Optional

from dotenv import load_dotenv


load_dotenv()

API_KEYS: List[str] = [
    key for key in [
        os.getenv("GOOGLE_API_KEY_1"),
        os.getenv("GOOGLE_API_KEY"),
        os.getenv("GOOGLE_API_KEY_2"),
        os.getenv("GOOGLE_API_KEY_3"),
        os.getenv("GOOGLE_API_KEY_4"),
    ] if key
]

SERP_API_KEY: Optional[str] = (
    os.getenv("SERP_API_KEY") or os.getenv("SERP_API_KEY_1")
)

DB_PATH: str = os.getenv("DB_PATH", "student_analyzer.db")
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
EMAIL_SENDER: Optional[str] = os.getenv("EMAIL_SENDER")


