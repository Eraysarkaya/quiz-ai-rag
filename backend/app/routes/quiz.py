"""
Quiz Routes
API endpoints for quiz generation and answer verification
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Header
from typing import Optional, Dict, List, Any
import uuid
import logging

from ..models.quiz import (
    QuizRequest, QuizResponse, QuizQuestion,
    AnswerVerifyRequest, AnswerVerifyResponse,
    TopicsResponse
)
from ..models.user import Database
from ..config import get_settings, POPULAR_TOPICS
from ..services.quiz_service import QuizService
from .auth import get_current_user, error_response

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quiz", tags=["Quiz"])
settings = get_settings()

# Singleton instances
_db = None
_quiz_service = None


def get_db() -> Database:
    """Get database instance."""
    global _db
    if _db is None:
        _db = Database(settings.data_dir)
    return _db


def get_quiz_service() -> QuizService:
    """Get quiz service instance."""
    global _quiz_service
    if _quiz_service is None:
        _quiz_service = QuizService()
    return _quiz_service


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    """
    Generate a quiz on the given topic.
    
    - **topic**: Science topic to generate questions about
    - **difficulty**: easy, medium, or hard
    - **num_questions**: Number of questions (1-10)
    """
    try:
        logger.info(f"Generating quiz: topic='{request.topic}', difficulty={request.difficulty.value}")
        
        quiz_service = get_quiz_service()
        result = await quiz_service.generate_quiz(
            topic=request.topic,
            difficulty=request.difficulty.value,
            num_questions=request.num_questions
        )
        
        if result.get("error"):
            logger.warning(f"Quiz generation failed: {result.get('message')}")
            return QuizResponse(
                success=False,
                topic=request.topic,
                difficulty=request.difficulty.value,
                error=result.get("message"),
                suggestions=result.get("suggestions", POPULAR_TOPICS[:5])
            )
        
        questions = [
            QuizQuestion(
                id=str(uuid.uuid4()),
                question=q["question"],
                options=q["options"],
                correct=q["correct"],
                explanation=q.get("explanation", ""),
                cached=q.get("cached", False)
            )
            for q in result.get("questions", [])
        ]
        
        logger.info(f"Quiz generated successfully: {len(questions)} questions")
        
        return QuizResponse(
            success=True,
            topic=request.topic,
            difficulty=request.difficulty.value,
            questions=questions
        )
        
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/verify", response_model=AnswerVerifyResponse)
async def verify_answer(request: AnswerVerifyRequest):
    """
    Verify if the selected answer is correct.
    
    The frontend sends the correct answer for comparison.
    Returns whether the selected answer matches and the explanation.
    """
    is_correct = request.selected_answer == request.correct_answer
    
    return AnswerVerifyResponse(
        correct=is_correct,
        correct_answer=request.correct_answer,
        explanation=request.explanation
    )


@router.get("/topics", response_model=TopicsResponse)
async def get_popular_topics_endpoint():
    """Get list of popular science topics."""
    return TopicsResponse(topics=POPULAR_TOPICS)


@router.post("/save")
async def save_quiz_attempt(
    topic: str = Body(...),
    difficulty: str = Body(...),
    questions: List[Dict[str, Any]] = Body(...),
    answers: Dict[str, str] = Body(...),
    score: int = Body(...),
    total: int = Body(...),
    authorization: str = Header(None)
):
    """
    Save quiz attempt.
    
    If authenticated, saves to user's history.
    If anonymous, still saves but not linked to a user.
    """
    db = get_db()
    
    # Try to get user from token, fallback to anonymous
    user_id = "anonymous"
    
    if authorization and authorization.startswith("Bearer "):
        try:
            from .auth import verify_token
            token = authorization.split(" ")[1]
            payload = verify_token(token)
            user_id = payload.get("sub", "anonymous")
        except Exception:
            pass  # Continue as anonymous
    
    try:
        attempt = db.save_quiz_attempt(
            user_id=user_id,
            topic=topic,
            difficulty=difficulty,
            questions=questions,
            answers=answers,
            score=score,
            total=total
        )
        logger.info(f"Quiz saved: user={user_id}, topic={topic}, score={score}/{total}")
        return {"success": True, "attempt_id": attempt.id, "user_id": user_id}
    except Exception as e:
        logger.error(f"Save quiz error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/history")
async def get_user_quiz_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get authenticated user's quiz history."""
    db = get_db()
    user_id = current_user['id']
    
    attempts = db.get_user_attempts(user_id, limit=limit)
    stats = db.get_user_stats(user_id)
    
    return {
        "stats": stats,
        "attempts": [a.model_dump() for a in attempts]
    }


# ============ Quiz Progress Endpoints ============

@router.post("/progress")
async def save_quiz_progress(
    topic: str = Body(...),
    difficulty: str = Body(...),
    questions: List[Dict[str, Any]] = Body(...),
    answers: Dict[str, str] = Body(...),
    current_index: int = Body(...),
    checked_questions: List[str] = Body(default=[]),
    current_user: dict = Depends(get_current_user)
):
    """
    Save in-progress quiz for syncing across devices.
    
    This allows users to continue quizzes on different devices.
    """
    db = get_db()
    user_id = current_user['id']
    
    try:
        progress = db.save_quiz_progress(
            user_id=user_id,
            topic=topic,
            difficulty=difficulty,
            questions=questions,
            answers=answers,
            current_index=current_index,
            checked_questions=checked_questions
        )
        logger.info(f"Quiz progress saved: user={user_id}, topic={topic}, index={current_index}")
        return {"success": True, "progress_id": progress.id}
    except Exception as e:
        logger.error(f"Save progress error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/progress")
async def get_quiz_progress(
    current_user: dict = Depends(get_current_user)
):
    """Get ALL user's in-progress quizzes."""
    db = get_db()
    user_id = current_user['id']
    
    # Get all in-progress quizzes
    all_progress = db.get_all_quiz_progress(user_id)
    
    if all_progress:
        return {
            "has_progress": True,
            "progress": all_progress[0].model_dump(),  # Most recent for backward compatibility
            "all_progress": [p.model_dump() for p in all_progress]  # All in-progress quizzes
        }
    return {"has_progress": False, "progress": None, "all_progress": []}


@router.delete("/progress")
async def delete_quiz_progress(
    topic: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Delete user's in-progress quiz. If topic specified, delete only that one."""
    db = get_db()
    user_id = current_user['id']
    
    deleted = db.delete_quiz_progress(user_id, topic)
    return {"success": True, "deleted": deleted}


# ============ NEW: Unified Quiz API ============

from pydantic import BaseModel

class QuizSaveRequest(BaseModel):
    """Request body for saving a quiz."""
    quiz_id: Optional[str] = None  # If provided, update existing quiz
    topic: str
    difficulty: str
    questions: List[Dict[str, Any]]
    answers: Dict[str, str] = {}
    current_index: int = 0
    score: int = 0
    status: str = "in_progress"  # "in_progress" | "completed"


@router.get("/quizzes")
async def get_user_quizzes(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get all quizzes for the current user (both in-progress and completed)."""
    db = get_db()
    user_id = current_user['id']
    
    quizzes = db.get_user_quizzes(user_id, limit=limit)
    
    return {
        "quizzes": [
            {
                "id": q.id,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "questions": q.questions,
                "answers": q.answers,
                "current_index": q.current_index,
                "score": q.score,
                "total": q.total,
                "percentage": q.percentage,
                "status": q.status,
                "is_completed": q.is_completed,
                "created_at": q.created_at.isoformat(),
                "updated_at": q.updated_at.isoformat()
            }
            for q in quizzes
        ]
    }


@router.post("/quizzes")
async def save_quiz(
    request: QuizSaveRequest,
    current_user: dict = Depends(get_current_user)
):
    """Save or update a quiz."""
    db = get_db()
    user_id = current_user['id']
    
    try:
        quiz = db.save_quiz(
            user_id=user_id,
            topic=request.topic,
            difficulty=request.difficulty,
            questions=request.questions,
            answers=request.answers,
            current_index=request.current_index,
            score=request.score,
            status=request.status,
            quiz_id=request.quiz_id
        )
        
        logger.info(f"Quiz saved: user={user_id}, quiz={quiz.id}, status={quiz.status}")
        
        return {
            "success": True,
            "quiz": {
                "id": quiz.id,
                "topic": quiz.topic,
                "difficulty": quiz.difficulty,
                "current_index": quiz.current_index,
                "score": quiz.score,
                "total": quiz.total,
                "status": quiz.status,
                "is_completed": quiz.is_completed,
                "updated_at": quiz.updated_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Save quiz error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/quizzes/{quiz_id}")
async def get_quiz_by_id(
    quiz_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific quiz by ID."""
    db = get_db()
    user_id = current_user['id']
    
    quiz = db.get_quiz(quiz_id, user_id)
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return {
        "quiz": {
            "id": quiz.id,
            "topic": quiz.topic,
            "difficulty": quiz.difficulty,
            "questions": quiz.questions,
            "answers": quiz.answers,
            "current_index": quiz.current_index,
            "score": quiz.score,
            "total": quiz.total,
            "percentage": quiz.percentage,
            "status": quiz.status,
            "is_completed": quiz.is_completed,
            "created_at": quiz.created_at.isoformat(),
            "updated_at": quiz.updated_at.isoformat()
        }
    }


@router.delete("/quizzes/{quiz_id}")
async def delete_quiz_by_id(
    quiz_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific quiz."""
    db = get_db()
    user_id = current_user['id']
    
    deleted = db.delete_quiz(quiz_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return {"success": True, "deleted": True}


@router.patch("/quizzes/{quiz_id}")
async def rename_quiz(
    quiz_id: str,
    body: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Rename a quiz (update topic)."""
    db = get_db()
    user_id = current_user['id']
    
    new_topic = body.get('topic')
    if not new_topic or not isinstance(new_topic, str):
        return error_response(
            status_code=400,
            code="INVALID_TOPIC",
            message="Topic is required and must be a string"
        )
    
    # Get existing quiz
    quiz = db.get_quiz(quiz_id, user_id)
    if not quiz:
        return error_response(
            status_code=404,
            code="QUIZ_NOT_FOUND",
            message="Quiz not found"
        )
    
    # Update the quiz with new topic
    updated = db.save_quiz(
        user_id=user_id,
        topic=new_topic.strip(),
        difficulty=quiz.difficulty,
        questions=quiz.questions,
        answers=quiz.answers,
        current_index=quiz.current_index,
        score=quiz.score,
        status=quiz.status,
        quiz_id=quiz_id
    )
    
    logger.info(f"Quiz renamed: {quiz_id} -> '{new_topic}'")
    
    return {
        "success": True,
        "quiz": {
            "id": updated.id,
            "topic": updated.topic,
            "updated_at": updated.updated_at.isoformat()
        }
    }
