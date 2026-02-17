from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StudentSignupRequest(BaseModel):
    username: str
    password: str
    course_id: str
    education_level: str
    admin_code: str


class LoginRequest(BaseModel):
    username: str
    password: str
    admin_code: str


class LoginResponse(BaseModel):
    user_id: int
    username: str
    course_id: Optional[str]
    education_level: Optional[str]


class ChangePasswordRequest(BaseModel):
    user_id: int
    new_password: str


class SignupRequest(BaseModel):
    username: str
    password: str
    course_id: str
    education_level: str
    admin_id: int


class CreateGroupRequest(BaseModel):
    group_name: str


class FileResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    uploaded_at: str


class SyllabusContent(BaseModel):
    syllabus_content: str
    ratings: Optional[Dict[str, int]] = None


class AnalysisResponse(BaseModel):
    analysis: str
    timetable: str
    roadmap: str
    timestamp: str


class QuizGenerateRequest(BaseModel):
    subject: str


class QuizModelResponse(BaseModel):
    subject: str
    questions: List[str]
    options: List[List[str]]
    answers: List[str]
    explanations: List[str]


class QuizGradeRequest(BaseModel):
    correct_answers: List[str]
    user_answers: List[str]


class QuizGradeResponse(BaseModel):
    marks: List[float]
    tot_mark: float


class QuizSaveRequest(BaseModel):
    subject: str
    questions: List[str]
    options: List[List[str]]
    correct_answers: List[str]
    user_answers: List[str]
    marks: List[float]
    explanations: List[str]
    related_content: List[str] = Field(default_factory=list)
    related_videos: List[str] = Field(default_factory=list)


class ChatTextRequest(BaseModel):
    user_id: int
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str


class ChatHistoryItem(BaseModel):
    role: str
    message: str
    timestamp: str

class ChatSession(BaseModel):
    id: str
    user_id: int
    group_id: int
    title: str
    created_at: str


class ImageChatRequest(BaseModel):
    user_id: int
    message: str
    session_id: str
    image_url: Optional[str] = None


class VideoChatRequest(BaseModel):
    user_id: int
    message: str
    session_id: str
    video_url: str


# --- Admin Schemas ---

class AdminCheckResponse(BaseModel):
    has_admin: bool


class AdminSetupRequest(BaseModel):
    username: str
    password: str
    email: str
    otp: str


class AdminGenerateOtpRequest(BaseModel):
    email: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    admin_id: int
    username: str
    admin_code: str
