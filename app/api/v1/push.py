from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.push import PushSettingsUpdate
from app.services.push_service import push_service

router = APIRouter(prefix="/push", tags=["消息推送"])


@router.get("/settings", response_model=ApiResponse, summary="获取推送设置")
async def get_settings(current_user: User = Depends(get_current_user)):
    return success(data=push_service.get_settings(current_user.id))


@router.put("/settings", response_model=ApiResponse, summary="更新推送设置")
async def update_settings(body: PushSettingsUpdate, current_user: User = Depends(get_current_user)):
    return success(data=push_service.update_settings(current_user.id, **body.model_dump()), message="推送设置已更新")


@router.get("/history", response_model=ApiResponse, summary="获取推送历史")
async def get_history(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session),
):
    return success(data=await push_service.get_history(db, current_user.id, page, page_size))
