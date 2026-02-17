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

# Handle Hugging Face Persistent Storage
# Handle Hugging Face Persistent Storage
print(f"[DEBUG] Checking storage configuration...")
print(f"[DEBUG] Root dirs: {os.listdir('/')}")
if os.path.exists("/data"):
    print(f"[DEBUG] /data exists. Permissions: {oct(os.stat('/data').st_mode)[-3:]}")
    try:
        # Test write permission
        test_file = "/data/.test_write"
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        print("[DEBUG] Write to /data successful.")
        
        if not os.getenv("DATABASE_URL"):
            DB_PATH: str = "/data/student_analyzer.db"
            print(f"[STORAGE] SUCCESS: Using persistent storage at {DB_PATH}")
    except Exception as e:
        print(f"[STORAGE] WARNING: /data exists but is not writable: {e}")
        DB_PATH: str = os.getenv("DB_PATH", "student_analyzer.db")
else:
    print("[DEBUG] /data directory does not exist.")
    DB_PATH: str = os.getenv("DB_PATH", "student_analyzer.db")

print(f"[STORAGE] Final DB_PATH: {DB_PATH}")

DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
EMAIL_SENDER: Optional[str] = os.getenv("EMAIL_SENDER")


