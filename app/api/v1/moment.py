"""
温馨瞬间路由
包含成长相册、时间线、分享下载等接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.services.moment_service import moment_service

router = APIRouter(prefix="/moment", tags=["温馨瞬间"])


@router.get("/timeline", response_model=ApiResponse, summary="获取温馨瞬间时间线")
async def get_moment_timeline(
    baby_id: int = Query(..., description="宝宝ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """按时间线获取宝宝的温馨瞬间列表"""
    result = await moment_service.get_timeline(db, user_id=current_user.id, baby_id=baby_id, page=page, page_size=page_size)
    return success(data=result)


@router.get("/month/{month}", response_model=ApiResponse, summary="按月查询温馨瞬间")
async def get_moments_by_month(
    month: str,
    baby_id: int = Query(..., description="宝宝ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """按月份查询温馨瞬间（格式：2024-01）"""
    result = await moment_service.get_by_month(db, user_id=current_user.id, baby_id=baby_id, month=month)
    return success(data=result)


@router.post("/share", response_model=ApiResponse, summary="分享温馨瞬间")
async def share_moment(
    moment_id: int = Query(..., description="瞬间ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """生成温馨瞬间的分享链接"""
    result = await moment_service.share_moment(db, user_id=current_user.id, moment_id=moment_id)
    return success(data=result, message="分享链接已生成")


@router.get("/download/{moment_id}", response_model=ApiResponse, summary="下载温馨瞬间")
async def download_moment(
    moment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取温馨瞬间的下载链接"""
    result = await moment_service.get_download_url(db, user_id=current_user.id, moment_id=moment_id)
    return success(data=result)
