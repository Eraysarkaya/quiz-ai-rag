"""
Backend Configuration
Environment variables and app settings
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Settings
    app_name: str = "Quiz AI"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # API Settings
    api_prefix: str = "/api"
    
    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Groq API
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Database paths
    data_dir: Path = Path(__file__).parent.parent / "data"
    chroma_db_path: Path = data_dir / "chroma_db"
    
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # Quiz Settings
    default_num_questions: int = 3
    max_questions: int = 10
    default_difficulty: str = "medium"
    
    # OOD Detection thresholds
    ood_high_threshold: float = 0.45
    ood_medium_threshold: float = 0.35
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Popular science topics for suggestions
POPULAR_TOPICS = [
    "Photosynthesis",
    "Cell biology",
    "DNA and genetics",
    "Chemical reactions",
    "Newton's laws of motion",
    "Electricity and magnetism",
    "Evolution",
    "Atomic structure",
    "Climate change",
    "Human body systems"
]
