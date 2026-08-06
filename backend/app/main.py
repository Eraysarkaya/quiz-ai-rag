"""
Quiz AI Backend - FastAPI Application
Main entry point for the API server
"""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .routes import quiz, auth, health
from .middleware import RateLimitMiddleware, SecurityHeadersMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific log levels
logging.getLogger("backend.app.core").setLevel(logging.INFO)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("faiss").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Quiz AI Backend...")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Ensure data directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    
    # Pre-warm models (optional - uncomment to enable)
    # logger.info("Pre-warming ML models...")
    # from .core.pipeline import QuizPipeline
    # QuizPipeline()  # Initialize singleton
    # logger.info("Models ready")
    
    yield
    
    logger.info("Shutting down Quiz AI Backend...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Quiz AI - Science MCQ Generator API powered by RAG + LLM",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware (100 requests per minute per IP)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_window=100,
    window_seconds=60,
    exclude_paths=["/api/health", "/docs", "/redoc", "/openapi.json", "/"]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(quiz.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)

# User routes (preferences, profile, data management)
from .routes import user
app.include_router(user.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health"
    }


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
