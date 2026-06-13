"""
宝宝管理路由
包含宝宝添加、查询、更新等接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.baby import BabyCreate, BabyUpdate
from app.services.baby_service import baby_service

router = APIRouter(prefix="/baby", tags=["宝宝管理"])


@router.post("/add", response_model=ApiResponse, summary="添加宝宝")
async def add_baby(
    body: BabyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """在当前家庭中添加一个宝宝档案"""
    result = await baby_service.add_baby(
        db, user_id=current_user.id,
        name=body.name, gender=body.gender, birth_date=body.birth_date, avatar_url=body.avatar_url,
    )
    return success(data=result, message="添加成功")


@router.get("/list", response_model=ApiResponse, summary="获取宝宝列表")
async def get_baby_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前家庭中的所有宝宝列表"""
    result = await baby_service.get_baby_list(db, user_id=current_user.id)
    return success(data=result)


@router.get("/{baby_id}", response_model=ApiResponse, summary="获取宝宝详情")
async def get_baby_detail(
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """根据ID获取宝宝详细信息"""
    result = await baby_service.get_baby_detail(db, user_id=current_user.id, baby_id=baby_id)
    return success(data=result)


@router.put("/{baby_id}", response_model=ApiResponse, summary="更新宝宝信息")
async def update_baby(
    baby_id: int,
    body: BabyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """更新宝宝信息"""
    await baby_service.update_baby(
        db, user_id=current_user.id, baby_id=baby_id,
        name=body.name, gender=body.gender, birth_date=body.birth_date, avatar_url=body.avatar_url,
    )
    return success(message="更新成功")


@router.delete("/{baby_id}", response_model=ApiResponse, summary="删除宝宝")
async def delete_baby(
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """删除宝宝档案"""
    await baby_service.delete_baby(db, user_id=current_user.id, baby_id=baby_id)
    return success(message="删除成功")
