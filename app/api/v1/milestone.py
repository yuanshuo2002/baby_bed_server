"""
成长记录路由
包含里程碑管理和AI周报相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.milestone import (
    MilestoneCreate, EventCaptureRequest, EventCaptureResponse,
    GIFGenerateRequest, WeeklyReportGenerateRequest, ReportInfo,
)
from app.services.milestone_service import milestone_service
from app.services.report_service import report_service

router = APIRouter(prefix="/milestone", tags=["成长记录"])


# ==================== 里程碑管理 ====================


@router.post("/create", response_model=ApiResponse, summary="创建里程碑")
async def create_milestone(
    body: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """为宝宝记录一个成长里程碑"""
    result = await milestone_service.create_milestone(
        db, user_id=current_user.id,
        baby_id=body.baby_id, event_type_id=body.event_type_id,
        milestone_code=body.milestone_code, milestone_name=body.milestone_name,
        milestone_desc=body.milestone_desc, age_months=body.age_months,
        snapshot_url=body.snapshot_url, gif_url=body.gif_url,
        video_clip_url=body.video_clip_url, detected_at=body.detected_at,
    )
    return success(data=result, message="创建成功")


@router.get("/list", response_model=ApiResponse, summary="获取里程碑列表")
async def get_milestone_list(
    baby_id: int = Query(..., description="宝宝ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取宝宝的里程碑记录列表"""
    result = await milestone_service.get_milestone_list(db, user_id=current_user.id, baby_id=baby_id, page=page, page_size=page_size)
    return success(data=result)


@router.get("/{milestone_id}", response_model=ApiResponse, summary="获取里程碑详情")
async def get_milestone_detail(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """根据ID获取里程碑详细信息"""
    result = await milestone_service.get_milestone_detail(db, user_id=current_user.id, milestone_id=milestone_id)
    return success(data=result)


@router.delete("/{milestone_id}", response_model=ApiResponse, summary="删除里程碑")
async def delete_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """删除里程碑记录"""
    await milestone_service.delete_milestone(db, user_id=current_user.id, milestone_id=milestone_id)
    return success(message="删除成功")


# ==================== AI周报 ====================


@router.post("/report/generate", response_model=ApiResponse, summary="生成成长报告")
async def generate_report(
    body: WeeklyReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """为宝宝生成成长报告（日报/周报/月报）"""
    result = await report_service.generate_weekly_report(
        db,
        user_id=current_user.id,
        baby_id=body.baby_id,
        report_type=body.report_type,
        period_start=body.period_start,
        period_end=body.period_end,
    )
    return success(data=result, message=f"{body.report_type}报告生成完成")


@router.get("/report/list", response_model=ApiResponse, summary="获取报告列表")
async def get_report_list(
    baby_id: int = Query(..., description="宝宝ID"),
    report_type: str = Query(None, description="报告类型: daily/weekly/monthly"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取宝宝的成长报告列表"""
    result = await report_service.get_weekly_report_list(
        db, user_id=current_user.id, baby_id=baby_id,
        report_type=report_type, page=page, page_size=page_size,
    )
    return success(data=result)


@router.get("/report/{report_id}", response_model=ApiResponse, summary="获取周报详情")
async def get_weekly_report_detail(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """根据ID获取AI周报详细信息"""
    result = await report_service.get_weekly_report_detail(db, user_id=current_user.id, report_id=report_id)
    return success(data=result)


# ========== 关键事件自动固化 (3.2) ==========
@router.post("/capture", response_model=ApiResponse, summary="截取事件视频")
async def capture_event_video(
    body: EventCaptureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """触发事件视频截取，截取前3s后5s视频片段"""
    result = await milestone_service.capture_event_video(
        db, user_id=current_user.id, baby_id=body.baby_id,
        event_type=body.event_type, trigger_time=body.trigger_time,
        pre_seconds=body.pre_seconds, post_seconds=body.post_seconds,
    )
    return success(data=result, message="视频截取任务已启动")


@router.post("/gif/generate", response_model=ApiResponse, summary="生成GIF动图")
async def generate_gif(
    body: GIFGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """将视频片段转换为GIF动图，要求<2MB"""
    result = await milestone_service.generate_gif(
        db, user_id=current_user.id, capture_id=body.capture_id,
        quality=body.quality, max_size_mb=body.max_size_mb,
    )
    return success(data=result, message="GIF生成完成")


