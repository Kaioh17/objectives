from fastapi import APIRouter

from app.schemas import Message

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
def health() -> Message:
    return Message(message="ok")
