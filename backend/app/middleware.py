"""
Rate Limiting Middleware for Quiz AI
Simple in-memory rate limiter for production use.
"""
import logging
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    
    Tracks requests per IP address and blocks if limit exceeded.
    """
    
    def __init__(
        self,
        app,
        requests_per_window: int = 100,
        window_seconds: int = 60,
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        
        # In-memory storage: {ip: (count, window_start)}
        self._requests: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, ip: str) -> Tuple[bool, int]:
        """
        Check if IP is rate limited.
        
        Returns:
            (is_limited, remaining_requests)
        """
        current_time = time.time()
        count, window_start = self._requests[ip]
        
        # Reset window if expired
        if current_time - window_start >= self.window_seconds:
            self._requests[ip] = (1, current_time)
            return False, self.requests_per_window - 1
        
        # Check limit
        if count >= self.requests_per_window:
            return True, 0
        
        # Increment count
        self._requests[ip] = (count + 1, window_start)
        return False, self.requests_per_window - count - 1
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        path = request.url.path
        
        # Skip rate limiting for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        is_limited, remaining = self._is_rate_limited(client_ip)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
