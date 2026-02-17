## Student Analyzer AI - FastAPI Backend

This backend mirrors the Streamlit app's features via REST:

- Auth (login, change password, admin user creation)
- File groups and uploads (text/pdf)
- Course and per-group syllabus with ratings
- Analysis (Gemini): analysis, timetable, roadmap
- Recommendations: YouTube, related websites
- Quiz: generate, grade, save, list
- Chat: text/image/video with history
- Performance: quiz history

### Setup

1. Install deps:

```bash
pip install -r requirements.txt
```

2. Environment (.env):

```bash
GOOGLE_API_KEY_1=your_key
SERP_API_KEY=optional_serp_key
```

3. Run:

```bash
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

Docs: http://localhost:8000/docs

### Key endpoints

- POST `/auth/login`
- POST `/auth/change-password`
- POST `/admin/users`
- GET/POST `/users/{user_id}/groups`
- POST `/groups/{group_id}/files`
- GET `/groups/{group_id}/files`
- DELETE `/files/{file_id}`
- GET/PUT `/courses/{course_id}/syllabus`
- GET/PUT `/groups/{group_id}/syllabus`
- POST/GET `/groups/{group_id}/analysis`
- GET `/recommendations/youtube?q=...`
- GET `/recommendations/web?q=...`
- POST `/groups/{group_id}/quizzes/generate`
- POST `/quizzes/grade`
- POST `/groups/{group_id}/quizzes/save?user_id=...`
- GET `/groups/{group_id}/quizzes?user_id=...`
- POST `/groups/{group_id}/chat/text`
- GET `/groups/{group_id}/chat/text?user_id=...`
- POST `/groups/{group_id}/chat/image`
- GET `/groups/{group_id}/chat/image/{image_id}?user_id=...`
- POST `/groups/{group_id}/chat/video`
- GET `/groups/{group_id}/chat/video/{video_id}?user_id=...`
- GET `/groups/{group_id}/performance?user_id=...`
- GET `/health`
