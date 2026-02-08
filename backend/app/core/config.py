from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Get the backend directory (parent of app directory)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "school_management"
    DATABASE_URL: Optional[str] = None

    # JWT settings
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Special School Management System"
    
    # Hugging Face settings
    HUGGINGFACE_API_TOKEN: Optional[str] = None

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        extra = 'ignore'

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()

# Debug: Print token status on import
if settings.HUGGINGFACE_API_TOKEN:
    print(f"✓ HUGGINGFACE_API_TOKEN loaded successfully (starts with: {settings.HUGGINGFACE_API_TOKEN[:10]}...)")
else:
    print("✗ WARNING: HUGGINGFACE_API_TOKEN not loaded! AI summarization will fail.") 