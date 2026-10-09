from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "groq_model": settings.GROQ_MODEL,
        "groq_api_key_configured": bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip()),
        "hitl_enabled": settings.HITL_ENABLED,
        "memory_enabled": settings.MEMORY_ENABLED
    }
