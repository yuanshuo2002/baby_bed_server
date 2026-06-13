"""
用户管理路由
包含主题配置、用户偏好设置等接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.device import ThemeConfig, ThemeConfigResponse
from app.services.user_service import user_service

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.get("/theme", response_model=ApiResponse, summary="获取主题配置")
async def get_theme_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前用户的主题配置"""
    result = await user_service.get_theme_config(db, user_id=current_user.id)
    return success(data=result)


@router.put("/theme", response_model=ApiResponse, summary="更新主题配置")
async def update_theme_config(
    body: ThemeConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """更新当前用户的主题配置"""
    result = await user_service.update_theme_config(
        db, user_id=current_user.id,
        theme_name=body.theme_name, primary_color=body.primary_color,
        font_size=body.font_size, animation_enabled=body.animation_enabled,
    )
    return success(data=result, message="主题配置已更新")
