"""
状态日志路由
包含状态日志、哭闹事件、危险事件、睡眠报告等接口

接口分类说明：
- 硬件接口（hardware_only）：仅硬件设备调用，无需用户认证
- 小程序接口：仅小程序端调用，需要用户认证
- 共用接口：硬件和小程序两端均可调用
"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.status import (
    StatusLogCreate, StatusLogInfo,
    CryEventCreate, CryEventHandle, CryEventInfo,
    DangerEventCreate, DangerEventHandle, DangerEventInfo,
    SleepReportInfo,
)
from app.services.status_service import status_service

router = APIRouter(prefix="/status", tags=["状态日志"])


# ==================== 硬件接口（无需用户认证） ====================
# 注意：以下接口保留用于兼容旧设备，新设备请使用 /sensor/detect 接口

@router.post("/log", response_model=ApiResponse, summary="[已废弃] 上报状态日志 [硬件接口]")
async def create_status_log(
    body: StatusLogCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """硬件端上报宝宝状态变化（熟睡/苏醒/高兴玩耍/哭闹/危险动作）"""
    data = body.model_dump()
    result = await status_service.create_status_log(db, data)
    return success(data=result, message="状态日志已记录")


@router.put("/log/{log_id}/end", response_model=ApiResponse, summary="[已废弃] 结束状态日志 [硬件接口]")
async def end_status_log(
    log_id: int,
    ended_at: datetime = Query(..., description="结束时间"),
    db: AsyncSession = Depends(get_db_session),
):
    """结束状态日志，计算持续时长"""
    result = await status_service.end_status_log(db, log_id, ended_at)
    return success(data=result)


@router.post("/cry", response_model=ApiResponse, summary="[已废弃] 上报哭闹事件 [硬件接口]")
async def create_cry_event(
    body: CryEventCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """硬件端上报哭闹事件，支持分级分类"""
    data = body.model_dump()
    result = await status_service.create_cry_event(db, data)
    return success(data=result, message="哭闹事件已记录")


@router.post("/danger", response_model=ApiResponse, summary="[已废弃] 上报危险事件 [硬件接口]")
async def create_danger_event(
    body: DangerEventCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """硬件端上报危险事件（呼吸暂停/靠近床边/翻床/站立等）"""
    data = body.model_dump()
    result = await status_service.create_danger_event(db, data)
    return success(data=result, message="危险事件已记录")


# ==================== 小程序接口（需要用户认证） ====================


@router.get("/history", response_model=ApiResponse, summary="获取状态历史 [小程序接口]")
async def get_status_history(
    baby_id: int = Query(..., description="宝宝ID"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """查询宝宝状态历史记录"""
    result = await status_service.get_status_history(db, baby_id, start_date, end_date)
    return success(data=result)


@router.post("/cry/{event_id}/handle", response_model=ApiResponse, summary="处理哭闹事件 [小程序接口]")
async def handle_cry_event(
    event_id: int,
    body: CryEventHandle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """父母处理哭闹事件"""
    result = await status_service.handle_cry_event(db, event_id, body.handle_method)
    return success(data=result, message="哭闹事件已处理")


@router.get("/cry/list", response_model=ApiResponse, summary="获取哭闹事件列表 [小程序接口]")
async def get_cry_events(
    baby_id: int = Query(..., description="宝宝ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """查询宝宝哭闹事件列表"""
    result = await status_service.get_cry_events(db, baby_id, page, page_size)
    return success(data=result)


@router.post("/danger/{event_id}/handle", response_model=ApiResponse, summary="处理危险事件 [小程序接口]")
async def handle_danger_event(
    event_id: int,
    body: DangerEventHandle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """父母处理危险事件"""
    result = await status_service.handle_danger_event(db, event_id, body.handle_result)
    return success(data=result, message="危险事件已处理")


@router.get("/danger/list", response_model=ApiResponse, summary="获取危险事件列表 [小程序接口]")
async def get_danger_events(
    baby_id: int = Query(..., description="宝宝ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """查询宝宝危险事件列表"""
    result = await status_service.get_danger_events(db, baby_id, page, page_size)
    return success(data=result)


# ========== 睡眠报告 ==========
@router.get("/sleep-report", response_model=ApiResponse, summary="获取睡眠报告 [小程序接口]")
async def get_sleep_report(
    baby_id: int = Query(..., description="宝宝ID"),
    report_date: date = Query(..., description="报告日期"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """查询指定日期的睡眠报告"""
    result = await status_service.get_sleep_report(db, baby_id, report_date)
    return success(data=result)


@router.post("/sleep-report/generate", response_model=ApiResponse, summary="生成睡眠报告 [小程序接口]")
async def generate_sleep_report(
    baby_id: int = Query(..., description="宝宝ID"),
    report_date: date = Query(..., description="报告日期"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """生成指定日期的睡眠报告"""
    result = await status_service.generate_sleep_report(db, baby_id, report_date)
    return success(data=result, message="睡眠报告已生成")
