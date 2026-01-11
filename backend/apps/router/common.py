"""
Common router
"""
from typing import Dict
from fastapi import HTTPException, Depends, APIRouter

from apps.utils.config import settings

router = APIRouter(tags=["Common"], prefix="/common")


@router.get("/health", summary="健康检查", description="检查服务的健康状态")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.API_V1_STR
    }
