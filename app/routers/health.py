"""
Health check endpoint.
"""

from fastapi import APIRouter
from app.schemas import HealthOut

router = APIRouter()


@router.get("/health", response_model=HealthOut)
async def health():
    return HealthOut()
