"""
User Routes - Profile, Preferences, Data Management
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Literal

from ..models.user import Database
from ..config import get_settings
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User"])
settings = get_settings()

# Singleton database
_db = None

def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database(settings.data_dir)
    return _db

# ============ Allowed Values ============
ALLOWED_DIFFICULTIES = ['easy', 'medium', 'hard']
ALLOWED_QUESTION_COUNTS = [3, 5, 10]

# ============ Request/Response Models ============

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None

class PreferencesResponse(BaseModel):
    default_difficulty: str
    default_question_count: int

class PreferencesUpdateRequest(BaseModel):
    default_difficulty: Optional[Literal['easy', 'medium', 'hard']] = None
    default_question_count: Optional[Literal[3, 5, 10]] = None

# ============ Helper ============

def error_response(status_code: int, code: str, message: str, details: dict = None) -> JSONResponse:
    content = {"error": {"code": code, "message": message}}
    if details:
        content["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=content)

# ============ Endpoints ============

@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(current_user = Depends(get_current_user)):
    """Get user preferences (returns defaults if none set)."""
    db = get_db()
    prefs = db.get_user_preferences(current_user["id"])
    return prefs

@router.patch("/preferences")
async def update_preferences(
    request: PreferencesUpdateRequest,
    current_user = Depends(get_current_user)
):
    """Update user preferences (partial update)."""
    db = get_db()
    
    # Validate values
    if request.default_difficulty and request.default_difficulty not in ALLOWED_DIFFICULTIES:
        return error_response(422, "INVALID_DIFFICULTY", f"Difficulty must be one of: {ALLOWED_DIFFICULTIES}")
    
    if request.default_question_count and request.default_question_count not in ALLOWED_QUESTION_COUNTS:
        return error_response(422, "INVALID_QUESTION_COUNT", f"Question count must be one of: {ALLOWED_QUESTION_COUNTS}")
    
    db.update_user_preferences(
        user_id=current_user["id"],
        default_difficulty=request.default_difficulty,
        default_question_count=request.default_question_count
    )
    
    # Return updated preferences
    prefs = db.get_user_preferences(current_user["id"])
    return {"success": True, "preferences": prefs}

@router.patch("/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    current_user = Depends(get_current_user)
):
    """Update user profile (name)."""
    db = get_db()
    
    if not request.name or len(request.name.strip()) == 0:
        return error_response(422, "INVALID_NAME", "Name cannot be empty")
    
    success = db.update_user(current_user["id"], name=request.name.strip())
    
    if success:
        user = db.get_user_by_id(current_user["id"])
        return {
            "success": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "picture": user.picture
            }
        }
    
    return error_response(500, "UPDATE_FAILED", "Failed to update profile")

@router.post("/clear-history")
async def clear_history(current_user = Depends(get_current_user)):
    """Delete ALL quiz data for the user."""
    db = get_db()
    deleted = db.clear_user_history(current_user["id"])
    return {"success": True, "deleted_count": deleted}

@router.delete("/account")
async def delete_account(current_user = Depends(get_current_user)):
    """Delete user account and all related data."""
    db = get_db()
    success = db.delete_user_account(current_user["id"])
    
    if success:
        return {"success": True, "message": "Account deleted successfully"}
    
    return error_response(500, "DELETE_FAILED", "Failed to delete account")
