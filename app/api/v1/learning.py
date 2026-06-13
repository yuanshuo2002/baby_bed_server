"""
学习进度路由
包含AI学习进度、个性化推荐等接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.services.learning_service import learning_service

router = APIRouter(prefix="/learning", tags=["学习进度"])


@router.get("/progress", response_model=ApiResponse, summary="获取学习进度")
async def get_learning_progress(
    baby_id: int = Query(..., description="宝宝ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取AI系统的学习进度和个性化优化状态"""
    result = await learning_service.get_progress(db, user_id=current_user.id, baby_id=baby_id)
    return success(data=result)


@router.get("/recommendations", response_model=ApiResponse, summary="获取个性化推荐")
async def get_recommendations(
    baby_id: int = Query(..., description="宝宝ID"),
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取基于学习数据的个性化推荐内容"""
    result = await learning_service.get_recommendations(db, user_id=current_user.id, baby_id=baby_id, limit=limit)
    return success(data=result)
