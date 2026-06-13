"""
被动响应路由
包含9大类别被动响应管理接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.services.event_service import event_service

router = APIRouter(prefix="/response", tags=["被动响应"])


@router.get("/event-types", response_model=ApiResponse, summary="获取被动事件类型列表")
async def get_passive_event_types(
    category: str | None = Query(None, description="事件大类筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取所有被动事件类型列表"""
    result = await event_service.get_passive_event_types(db, category=category)
    return success(data=result)


@router.get("/event-types/{event_type_id}", response_model=ApiResponse, summary="获取事件类型详情")
async def get_event_type_detail(
    event_type_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """根据ID获取被动事件类型的详细信息"""
    result = await event_service.get_event_type_detail(db, event_type_id=event_type_id)
    return success(data=result)


@router.put("/event-types/{event_type_id}", response_model=ApiResponse, summary="更新事件类型配置")
async def update_event_type(
    event_type_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """更新被动事件类型的配置"""
    result = await event_service.update_event_type(db, event_type_id=event_type_id)
    return success(data=result, message="更新成功")


@router.post("/trigger", response_model=ApiResponse, summary="手动触发被动响应")
async def trigger_passive_response(
    event_type_id: int,
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """手动触发一次被动响应"""
    result = await event_service.trigger_passive_response(
        db, event_type_id=event_type_id, baby_id=baby_id,
    )
    return success(data=result, message="被动响应已触发")


@router.get("/history", response_model=ApiResponse, summary="获取被动响应历史")
async def get_response_history(
    baby_id: int = Query(..., description="宝宝ID"),
    category: str | None = Query(None, description="事件大类"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取被动响应的历史记录"""
    result = await event_service.get_response_history(
        db, user_id=current_user.id, baby_id=baby_id,
        category=category, page=page, page_size=page_size,
    )
    return success(data=result)
