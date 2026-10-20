from fastapi import APIRouter

from app.router import auth, calendar, health, objectives, users

# Versioned routes; mounted under settings.api_prefix in main.py
api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(objectives.router)
api_router.include_router(calendar.router)

__all__ = ["api_router", "health"]
