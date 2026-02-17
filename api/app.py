from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import google.generativeai as genai

# --- FIX: Load environment variables and configure Google API ---
# This loads the variables from your .env file into the environment
load_dotenv()

# This configures the google-generativeai library with your primary API key at startup
# It's a good practice to have a default key configured.
# Your other functions can still rotate keys if this one is rate-limited.
api_key = os.getenv("GOOGLE_API_KEY_1") or os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("WARNING: GOOGLE_API_KEY_1 or GOOGLE_API_KEY not found. Some features may not work.")
# ----------------------------------------------------------------

from .db import init_db
from .routers.auth import router as auth_router
from .routers.admin import router as admin_router
from .routers.groups_files import router as groups_files_router
from .routers.syllabus import router as syllabus_router
from .routers.analysis import router as analysis_router
from .routers.recommendations import router as rec_router
from .routers.quiz import router as quiz_router
from .routers.chat import router as chat_router
from .routers.health import router as health_router
from .routers.performance import router as perf_router


def create_app() -> FastAPI:
    app = FastAPI(title="Student Analyzer AI - FastAPI Backend", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure DB is initialized
    init_db()

    # Routers
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(groups_files_router)
    app.include_router(syllabus_router)
    app.include_router(analysis_router)
    app.include_router(rec_router)
    app.include_router(quiz_router)
    app.include_router(chat_router)
    app.include_router(health_router)
    app.include_router(perf_router)

    @app.get("/")
    def root():
        return {"status": "online", "message": "LMS Backend is running"}

    return app


app = create_app()
