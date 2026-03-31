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
origins = [
    "http://localhost:3000",  # React frontend
    "http://localhost:5173",  # Vite frontend (if using Vite)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API router with the v1 prefix
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Special School Management System API",
        "docs": "/docs",  # Swagger UI
        "redoc": "/redoc"  # ReDoc UI
    }
