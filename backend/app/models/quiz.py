"""
Pydantic Models for Quiz API
Request and Response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class Difficulty(str, Enum):
    """Quiz difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ============ Quiz Models ============

class QuizRequest(BaseModel):
    """Request to generate a quiz."""
    topic: str = Field(..., min_length=2, max_length=200, description="Science topic")
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM)
    num_questions: int = Field(default=3, ge=1, le=10)


class QuizOption(BaseModel):
    """Single quiz option."""
    label: str  # A, B, C, D
    text: str


class QuizQuestion(BaseModel):
    """Single quiz question."""
    id: str
    question: str
    options: Dict[str, str]  # {"A": "...", "B": "...", ...}
    correct: str  # Correct option label
    explanation: str
    cached: bool = False


class QuizResponse(BaseModel):
    """Quiz generation response."""
    success: bool
    topic: str
    difficulty: str
    questions: List[QuizQuestion] = []
    error: Optional[str] = None
    suggestions: Optional[List[str]] = None  # For OOD topics


class AnswerVerifyRequest(BaseModel):
    """Request to verify an answer."""
    question_id: str
    selected_answer: str
    correct_answer: str  # The correct answer for verification
    explanation: str = ""  # Explanation to return


class AnswerVerifyResponse(BaseModel):
    """Answer verification response."""
    correct: bool
    correct_answer: str
    explanation: str


# ============ User Models ============

class UserBase(BaseModel):
    """Base user model."""
    email: str
    name: str
    picture: Optional[str] = None


class UserCreate(UserBase):
    """User creation from Google OAuth."""
    google_id: str


class User(UserBase):
    """Full user model with ID."""
    id: str
    google_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """User stored in database."""
    pass


# ============ Quiz History Models ============

class QuizAttempt(BaseModel):
    """Single quiz attempt by user."""
    id: str
    user_id: str
    topic: str
    difficulty: str
    questions: List[QuizQuestion]
    answers: Dict[str, str]  # {question_id: selected_answer}
    score: int
    total: int
    percentage: float
    created_at: datetime


class QuizHistoryResponse(BaseModel):
    """User's quiz history."""
    total_quizzes: int
    total_questions: int
    correct_answers: int
    average_score: float
    attempts: List[QuizAttempt]


# ============ Auth Models ============

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: Optional[str] = None
    email: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    """Google OAuth code exchange request."""
    code: str
    redirect_uri: str


# ============ Topic Models ============

class TopicsResponse(BaseModel):
    """Popular topics response."""
    topics: List[str]


# ============ Health Check ============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    services: Dict[str, bool]
