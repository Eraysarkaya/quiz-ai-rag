"""
Google OAuth Authentication Service
Handles Google sign-in and JWT token generation
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..config import get_settings
from ..models.user import Database, UserDB

settings = get_settings()
security = HTTPBearer(auto_error=False)


class AuthService:
    """Authentication service for Google OAuth and JWT."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def verify_google_token(self, token: str) -> dict:
        """Verify Google ID token and return user info."""
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.google_client_id
            )
            
            # Verify issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return {
                "google_id": idinfo['sub'],
                "email": idinfo['email'],
                "name": idinfo.get('name', ''),
                "picture": idinfo.get('picture', '')
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(e)}"
            )
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
        to_encode = {
            "sub": user_id,
            "email": email,
            "exp": expire
        }
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def authenticate_or_create_user(self, google_token: str) -> tuple[UserDB, str]:
        """Authenticate with Google token or create new user."""
        # Verify Google token
        google_info = await self.verify_google_token(google_token)
        
        # Check if user exists
        user = self.db.get_user_by_google_id(google_info["google_id"])
        
        if not user:
            # Create new user
            user = self.db.create_user(
                google_id=google_info["google_id"],
                email=google_info["email"],
                name=google_info["name"],
                picture=google_info.get("picture")
            )
        
        # Generate JWT
        access_token = self.create_access_token(user.id, user.email)
        
        return user, access_token


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Database = None
) -> Optional[UserDB]:
    """Get current user from JWT token (optional)."""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.get_user_by_id(user_id)
        return user
    except JWTError:
        return None


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Require authentication, raise 401 if not authenticated."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
