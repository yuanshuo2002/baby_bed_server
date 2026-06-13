"""
作息管理路由
包含作息创建、查询、冲突检测、优化建议、提醒等接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.routine import (
    RoutineCreate, RoutineUpdate,
    EASYTemplateRequest, EASYTemplateResponse,
    RoutineOptimizeRequest, RoutineOptimizeResponse,
    ConflictCheckRequest, ConflictCheckResponse, RoutineFixRequest,
)
from app.services.routine_service import routine_service

router = APIRouter(prefix="/routine", tags=["作息管理"])


@router.post("/create", response_model=ApiResponse, summary="创建作息计划")
async def create_routine(
    body: RoutineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """为宝宝创建一条作息计划"""
    result = await routine_service.create_routine(
        db, user_id=current_user.id,
        baby_id=body.baby_id, template_name=body.template_name,
        age_month_min=body.age_month_min, age_month_max=body.age_month_max,
        time_slot=body.time_slot, activity_type=body.activity_type,
        activity_name=body.activity_name, duration_min=body.duration_min,
        reminder_enabled=body.reminder_enabled, reminder_before_min=body.reminder_before_min,
        effective_date=body.effective_date, expire_date=body.expire_date,
    )
    return success(data=result, message="创建成功")


@router.get("/list", response_model=ApiResponse, summary="获取作息列表")
async def get_routine_list(
    baby_id: int = Query(..., description="宝宝ID"),
    activity_type: str | None = Query(None, description="活动类型筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取指定宝宝的所有作息计划"""
    result = await routine_service.get_routine_list(db, user_id=current_user.id, baby_id=baby_id, activity_type=activity_type)
    return success(data=result)


@router.get("/{routine_id}", response_model=ApiResponse, summary="获取作息详情")
async def get_routine_detail(
    routine_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """根据ID获取作息计划详情"""
    result = await routine_service.get_routine_detail(db, user_id=current_user.id, routine_id=routine_id)
    return success(data=result)


@router.put("/{routine_id}", response_model=ApiResponse, summary="更新作息计划")
async def update_routine(
    routine_id: int,
    body: RoutineUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """更新作息计划"""
    await routine_service.update_routine(
        db, user_id=current_user.id, routine_id=routine_id,
        template_name=body.template_name, time_slot=body.time_slot,
        activity_type=body.activity_type, activity_name=body.activity_name,
        duration_min=body.duration_min, reminder_enabled=body.reminder_enabled,
        reminder_before_min=body.reminder_before_min, expire_date=body.expire_date,
        is_active=body.is_active,
    )
    return success(message="更新成功")


@router.delete("/{routine_id}", response_model=ApiResponse, summary="删除作息计划")
async def delete_routine(
    routine_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """删除作息计划"""
    await routine_service.delete_routine(db, user_id=current_user.id, routine_id=routine_id)
    return success(message="删除成功")


@router.get("/conflicts/{baby_id}", response_model=ApiResponse, summary="查询作息冲突")
async def get_routine_conflicts(
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """查询指定宝宝的作息冲突记录"""
    result = await routine_service.get_conflicts(db, user_id=current_user.id, baby_id=baby_id)
    return success(data=result)


@router.get("/optimize/{baby_id}", response_model=ApiResponse, summary="获取作息优化建议")
async def get_routine_optimization(
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """基于AI分析获取作息优化建议"""
    result = await routine_service.get_optimization(db, user_id=current_user.id, baby_id=baby_id)
    return success(data=result)


@router.get("/today/{baby_id}", response_model=ApiResponse, summary="获取今日作息安排")
async def get_today_routines(
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取宝宝今日的作息安排"""
    result = await routine_service.get_today_routines(db, user_id=current_user.id, baby_id=baby_id)
    return success(data=result)


# ========== EASY模式作息引导 (2.3) ==========
@router.get("/easy/template", response_model=ApiResponse, summary="获取EASY模式模板")
async def get_easy_template(
    baby_id: int = Query(..., description="宝宝ID"),
    age_month: int = Query(..., ge=0, le=48, description="宝宝月龄(0-48)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取0-48月龄EASY模式作息模板"""
    result = await routine_service.get_easy_template(db, user_id=current_user.id, baby_id=baby_id, age_month=age_month)
    return success(data=result)


@router.post("/easy/optimize", response_model=ApiResponse, summary="优化作息计划")
async def optimize_routine(
    body: RoutineOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """基于历史数据优化作息计划，实现7天循环自动迭代"""
    result = await routine_service.optimize_routine(db, user_id=current_user.id, baby_id=body.baby_id, analysis_days=body.analysis_days)
    return success(data=result)


# ========== 作息冲突检测与优化 (2.4) ==========
@router.post("/conflict/check", response_model=ApiResponse, summary="检测作息冲突")
async def check_routine_conflicts(
    body: ConflictCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """检测7天内的作息冲突，生成优化建议"""
    result = await routine_service.check_conflicts(db, user_id=current_user.id, baby_id=body.baby_id, check_days=body.check_days)
    return success(data=result)


@router.post("/conflict/fix", response_model=ApiResponse, summary="修复作息冲突")
async def fix_routine_conflicts(
    body: RoutineFixRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """自动或手动修复作息冲突，重新生成计划"""
    result = await routine_service.fix_routine(db, user_id=current_user.id, baby_id=body.baby_id, fix_type=body.fix_type, conflict_ids=body.conflict_ids)
    return success(data=result, message="作息冲突已修复")
