from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    session_id: str
    suggestions: Optional[List[str]] = None


class UsageInfo(BaseModel):
    """Rate limiting usage information."""
    plan: str
    used: int
    limit: int
    remaining: int
    resets_at: Optional[str] = None
    message: Optional[str] = None


class ResumeUploadResponse(BaseModel):
    session_id: str
    message: str
    resume_text: str
    initial_analysis: str
    usage: Optional[UsageInfo] = None


class ResumeSection(BaseModel):
    name: str
    content: str
    score: Optional[int] = None
    suggestions: List[str] = []


class ResumeAnalysis(BaseModel):
    overall_score: int
    ats_score: int
    sections: List[ResumeSection]
    strengths: List[str]
    improvements: List[str]
    industry_fit: str
    target_companies: List[str]


class SessionState(BaseModel):
    session_id: str
    resume_text: Optional[str] = None
    resume_analysis: Optional[ResumeAnalysis] = None
    conversation_history: List[Message] = []
    user_info: Dict[str, Any] = {}
    user_corrections: List[str] = []  # Track user corrections to prevent hallucinations
    created_at: datetime = Field(default_factory=datetime.utcnow)
