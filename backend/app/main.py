from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Ensure absolute imports like "from app..." work when starting with
# "uvicorn backend.app.main:app" from repository root (e.g., on Render).
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api.api import api_router
from app.core.config import settings

app = FastAPI(
    title="Special School Management System",
    description="API for managing special school students, teachers, and resources",
    version="1.0.0"
)

# Configure CORS
if settings.CORS_ORIGINS and settings.CORS_ORIGINS.strip():
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:3000",  # React frontend
        "http://localhost:5173",  # Vite frontend (if using Vite)
    ]

# Allow deployed frontend URLs via environment variables.
# Example: FRONTEND_URL=https://your-frontend.onrender.com
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

frontend_urls = os.getenv("FRONTEND_URLS")
if frontend_urls:
    origins.extend([url.strip() for url in frontend_urls.split(",") if url.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API router with the v1 prefix
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
@app.head("/")
async def root():
    return {
        "message": "Welcome to Special School Management System API",
        "docs": "/docs",  # Swagger UI
        "redoc": "/redoc"  # ReDoc UI
    }

