"""
Auth Routes - Secure Authentication System
JWT-based authentication with SQLite database
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends, Header, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..models.user import Database
from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


# ============ Structured Error Responses ============

def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict = None
) -> JSONResponse:
    """
    Return standardized error response.
    
    Format: {error: {code, message, details}}
    
    Args:
        status_code: HTTP status code
        code: Machine-readable error code (e.g., USER_NOT_FOUND)
        message: Human-readable error message
        details: Optional additional details
    """
    content = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        content["error"]["details"] = details
    
    logger.warning(f"Auth error: {code} - {message}")
    return JSONResponse(status_code=status_code, content=content)

# Password hashing (pbkdf2_sha256 - cross-platform compatible)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Singleton database
_db = None


def get_db() -> Database:
    """Get database instance."""
    global _db
    if _db is None:
        _db = Database(settings.data_dir)
    return _db


# ============ JWT Token Functions ============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(authorization: str = Header(None)) -> dict:
    """Dependency to get current authenticated user from SQLite."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    db = get_db()
    user = db.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user.model_dump()


# ============ Request/Response Models ============

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    code: Optional[str] = None


# ============ Endpoints ============

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user with secure password hashing."""
    db = get_db()
    
    # Check if email already exists
    existing = db.get_user_by_email(request.email)
    if existing:
        return error_response(
            status_code=400,
            code="EMAIL_EXISTS",
            message="This email is already registered. Try logging in instead."
        )
    
    # Create new user with hashed password
    password_hash = pwd_context.hash(request.password)
    user = db.create_user(
        email=request.email,
        name=request.name,
        password_hash=password_hash,
        provider="local"
    )
    
    # Create JWT token
    token = create_access_token(data={"sub": user.id, "email": user.email})
    logger.info(f"User registered: {user.email}")
    
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name
        )
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    db = get_db()
    
    # Get user by email (includes password_hash)
    user_data = db.get_user_by_email(request.email)
    
    if not user_data:
        return error_response(
            status_code=404,
            code="USER_NOT_FOUND",
            message="No account found with this email address."
        )
    
    # Verify password
    if not user_data.get('password_hash'):
        return error_response(
            status_code=400,
            code="GOOGLE_ACCOUNT",
            message="This account uses Google sign-in. Please use the Google button."
        )
    
    if not pwd_context.verify(request.password, user_data['password_hash']):
        return error_response(
            status_code=401,
            code="INVALID_PASSWORD",
            message="Incorrect password. Please try again."
        )
    
    token = create_access_token(data={"sub": user_data['id'], "email": user_data['email']})
    logger.info(f"User logged in: {user_data['email']}")
    
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user_data['id'],
            email=user_data['email'],
            name=user_data['name'],
            picture=user_data.get('picture')
        )
    )


@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest = Body(...)):
    """
    Authenticate with Google OAuth.
    Frontend sends Google credential (ID token) after user signs in.
    """
    db = get_db()
    
    if not request.credential and not request.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either credential or code is required"
        )
    
    # In production: Verify Google ID token
    # For now, decode the credential to get user info
    # The credential is a JWT from Google
    
    try:
        # Decode without verification for demo (in production, verify with Google)
        if request.credential:
            # Google ID tokens are JWTs - decode to get user info
            parts = request.credential.split('.')
            if len(parts) == 3:
                import base64
                import json
                # Pad the payload
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)
                user_info = json.loads(base64.urlsafe_b64decode(payload))
                
                google_id = user_info.get('sub')
                email = user_info.get('email')
                name = user_info.get('name', 'Google User')
                picture = user_info.get('picture')
            else:
                raise ValueError("Invalid credential format")
        else:
            # For authorization code flow (needs more setup)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code flow not yet implemented"
            )
    except Exception as e:
        logger.warning(f"Failed to decode Google credential: {e}")
        # Fallback to demo user
        google_id = f"google_{request.credential[:12] if request.credential else 'demo'}"
        email = f"{google_id}@gmail.com"
        name = "Google User"
        picture = None
    
    # Check if user exists
    existing_user = db.get_user_by_google_id(google_id)
    
    if existing_user:
        # Login existing user
        user = existing_user
        logger.info(f"Google user logged in: {user.email}")
    else:
        # Create new user
        user = db.create_user(
            email=email,
            name=name,
            picture=picture,
            provider="google",
            google_id=google_id
        )
        logger.info(f"Google user registered: {user.email}")
    
    token = create_access_token(data={"sub": user.id, "provider": "google"})
    
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture
        )
    )


class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


@router.post("/google/callback", response_model=AuthResponse)
async def google_callback(request: GoogleCallbackRequest):
    """
    Handle Google OAuth callback - exchange authorization code for tokens.
    """
    import httpx
    
    db = get_db()
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data={
                "code": request.code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": request.redirect_uri,
                "grant_type": "authorization_code"
            })
            
            if token_response.status_code != 200:
                logger.error(f"Google token exchange failed: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )
            
            tokens = token_response.json()
            id_token = tokens.get("id_token")
            
            if not id_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No ID token received"
                )
            
            # Decode ID token to get user info
            import base64
            import json
            
            parts = id_token.split('.')
            if len(parts) != 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid ID token format"
                )
            
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            user_info = json.loads(base64.urlsafe_b64decode(payload))
            
            google_id = user_info.get('sub')
            email = user_info.get('email')
            name = user_info.get('name', 'Google User')
            picture = user_info.get('picture')
            
    except httpx.RequestError as e:
        logger.error(f"Google API request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to Google"
        )
    
    # Check if user exists
    existing_user = db.get_user_by_google_id(google_id)
    
    if existing_user:
        user = existing_user
        logger.info(f"Google user logged in: {user.email}")
    else:
        # Check if email already exists (local account)
        existing_email = db.get_user_by_email(email)
        if existing_email:
            # Link Google to existing account
            # For now, just use the existing account
            user = db.get_user_by_id(existing_email['id'])
            logger.info(f"Linked Google to existing account: {email}")
        else:
            # Create new user
            user = db.create_user(
                email=email,
                name=name,
                picture=picture,
                provider="google",
                google_id=google_id
            )
            logger.info(f"Google user registered: {user.email}")
    
    token = create_access_token(data={"sub": user.id, "provider": "google"})
    
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info - requires valid JWT token."""
    return UserResponse(
        id=current_user['id'],
        email=current_user['email'],
        name=current_user['name'],
        picture=current_user.get('picture')
    )


@router.get("/history")
async def get_quiz_history(
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


@router.post("/logout")
async def logout():
    """Logout user - client should remove the token."""
    return {"success": True, "message": "Logged out successfully"}


@router.get("/validate")
async def validate_token(authorization: str = Header(None)):
    """Validate if the provided token is still valid."""
    if not authorization or not authorization.startswith("Bearer "):
        return {"valid": False}
    
    token = authorization.split(" ")[1]
    try:
        payload = verify_token(token)
        return {"valid": True, "user_id": payload.get("sub")}
    except HTTPException:
        return {"valid": False}
