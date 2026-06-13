"""
婴儿互动路由 - 精简版
仅包含核心接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.interaction import InteractionContentRequest, InteractionHistoryRecord
from app.models.baby import Baby
from app.services.family_service import FamilyService
from sqlalchemy import select

router = APIRouter(prefix="/interaction", tags=["婴儿互动"])
_interaction_history: list[dict] = []


async def _check_baby(db: AsyncSession, user_id: int, baby_id: int) -> None:
    family = await FamilyService._get_user_family_obj(db, user_id)
    result = await db.execute(select(Baby.id).where(Baby.id == baby_id, Baby.family_id == family.id))
    if result.scalar_one_or_none() is None:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("宝宝不存在")


@router.post("/content", response_model=ApiResponse, summary="创建互动内容")
async def create_content(
    body: InteractionContentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """创建互动内容(音乐/儿歌/故事/游戏/运动)"""
    await _check_baby(db, current_user.id, body.baby_id)
    content_id = len(_interaction_history) + 1
    record = {"content_id": content_id, **body.model_dump(), "interaction_type": "play"}
    _interaction_history.append(record)
    return success(data=record, message="内容创建成功")


@router.get("/library", response_model=ApiResponse, summary="获取资源库")
async def get_library(
    baby_id: int = Query(..., description="宝宝ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取互动资源库(基于宝宝月龄和状态推荐)"""
    await _check_baby(db, current_user.id, baby_id)
    return success(data={
        "library": [
            {"id": 1, "name": "摇篮曲", "type": "music", "duration_sec": 180},
            {"id": 2, "name": "小白兔", "type": "song", "duration_sec": 120},
            {"id": 3, "name": "狼来了", "type": "story", "duration_sec": 300},
        ]
    })


@router.get("/history", response_model=ApiResponse, summary="获取互动历史")
async def get_history(
    baby_id: int = Query(..., description="宝宝ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取宝宝互动历史记录"""
    await _check_baby(db, current_user.id, baby_id)
    return success(data={"history": [item for item in _interaction_history if item["baby_id"] == baby_id]})
