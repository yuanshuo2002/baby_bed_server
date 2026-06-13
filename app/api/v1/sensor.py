"""
智能监测路由
包含雷达/视觉/音频采集、事件检测、事件查询、事件确认等接口

接口分类说明：
- 硬件接口（hardware_only）：仅硬件设备调用，无需用户认证
- 小程序接口：仅小程序端调用，需要用户认证
- 共用接口：硬件和小程序两端均可调用
"""
from datetime import datetime
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.models.device import Device
from app.schemas.base import ApiResponse
from app.schemas.event import EventConfirm
from app.schemas.sensor import SensorDataUpload, SensorFusionRequest, SensorFusionResponse, SceneClassifyResponse, SceneResponseRequest, SceneResponseScript
from app.services.sensor_service import sensor_service
from app.services.event_service import event_service

router = APIRouter(prefix="/sensor", tags=["智能监测"])


# ==================== 硬件接口（无需用户认证） ====================

@router.post("/upload", response_model=ApiResponse, summary="上传传感器数据 [硬件接口]")
async def upload_sensor_data(
    body: SensorDataUpload,
    db: AsyncSession = Depends(get_db_session),
):
    """设备上传传感器原始数据（硬件端调用）
    如果未传 baby_id，自动通过 device_sn 查询绑定状态
    """
    # 如果未传 baby_id，尝试通过 device_sn 查询
    baby_id = body.baby_id
    if baby_id is None:
        result = await db.execute(
            select(Device.baby_id).where(Device.device_sn == body.device_sn)
        )
        baby_id = result.scalar_one_or_none()

    result = await sensor_service.upload_sensor_data(
        db, device_sn=body.device_sn, baby_id=baby_id, collected_at=body.collected_at,
        breath_rate=body.breath_rate, heart_rate=body.heart_rate, body_movement=body.body_movement,
        distance_cm=body.distance_cm, sound_db=body.sound_db, sound_type=body.sound_type,
        pose_status=body.pose_status, face_detected=body.face_detected, expression=body.expression,
        body_offset_cm=body.body_offset_cm, roll_angle=body.roll_angle, height_cm=body.height_cm,
        room_temp=body.room_temp, humidity=body.humidity, noise_db=body.noise_db,
    )
    return success(data=result, message="数据上传成功")


@router.post("/status/upload", response_model=ApiResponse, summary="上传婴儿状态 [硬件接口]")
async def upload_baby_status(
    device_sn: str = Query(..., description="设备序列号"),
    baby_id: int | None = Query(None, description="宝宝ID（可选）"),
    status_type: str = Query(..., description="状态类型: sleeping/awake/playing/crying/danger"),
    status_level: int = Query(0, ge=0, le=3, description="风险等级: 0=正常, 1=轻微, 2=警告, 3=危险"),
    started_at: datetime = Query(..., description="状态开始时间"),
    breath_rate: float | None = Query(None, description="呼吸频率"),
    heart_rate: float | None = Query(None, description="心率"),
    pose_status: str | None = Query(None, description="姿态"),
    expression: str | None = Query(None, description="表情"),
    db: AsyncSession = Depends(get_db_session),
):
    """上传婴儿状态及风险等级到数据库（硬件端调用）
    由硬件端本地AI判断状态后上传
    """
    result = await sensor_service.upload_status(
        db, device_sn=device_sn, baby_id=baby_id,
        status_type=status_type, status_level=status_level, started_at=started_at,
        breath_rate=breath_rate, heart_rate=heart_rate, pose_status=pose_status, expression=expression,
    )
    if not result.get("success", True):
        return success(data=result, message=result.get("message", "状态上传失败"))
    return success(data=result, message="状态上传成功")


@router.post("/upload-file", response_model=ApiResponse, summary="上传传感器数据文件 [硬件接口]")
async def upload_sensor_file(
    device_sn: str = Form(..., description="设备序列号"),
    baby_id: int = Form(..., description="宝宝ID"),
    file: UploadFile = File(..., description="数据文件"),
    db: AsyncSession = Depends(get_db_session),
):
    """上传传感器数据文件（硬件端调用）"""
    result = await sensor_service.upload_sensor_file(
        db, device_sn=device_sn, baby_id=baby_id, file=file,
    )
    return success(data=result, message="文件上传成功")


@router.post("/detect", response_model=ApiResponse, summary="触发事件检测 [硬件接口]")
async def trigger_detection(
    device_sn: str,
    db: AsyncSession = Depends(get_db_session),
):
    """触发设备事件检测，基于最新传感器数据进行五类状态分类
    检测到状态变化时自动写入 baby_status_log 表
    哭闹/危险状态同步创建 cry_event / danger_event"""
    result = await sensor_service.trigger_detection(
        db, device_sn=device_sn,
    )
    return success(data=result, message="检测完成")


@router.get("/status/current", response_model=ApiResponse, summary="获取设备当前状态 [硬件接口]")
async def get_current_status(
    device_sn: str = Query(..., description="设备序列号"),
    db: AsyncSession = Depends(get_db_session),
):
    """获取设备当前状态（通过 device_sn，无需认证）"""
    result = await sensor_service.get_device_current_status(db, device_sn)
    return success(data=result)


@router.get("/status/history", response_model=ApiResponse, summary="获取设备状态历史 [硬件接口]")
async def get_status_history_by_device(
    device_sn: str = Query(..., description="设备序列号"),
    db: AsyncSession = Depends(get_db_session),
):
    """获取设备状态历史记录（通过 device_sn，无需认证）"""
    result = await sensor_service.get_device_status_history(db, device_sn)
    return success(data=result)


# ==================== 共用接口（硬件和小程序均可用） ====================


@router.get("/events", response_model=ApiResponse, summary="查询监测事件列表 [共用接口]")
async def get_events(
    device_sn: str | None = Query(None, description="设备序列号"),
    baby_id: int | None = Query(None, description="宝宝ID"),
    event_type_id: str | None = Query(None, description="事件类型ID"),
    event_level: str | None = Query(None, description="事件级别"),
    page: str | None = Query(None, description="页码"),
    page_size: str | None = Query(None, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """查询监测事件列表"""
    # 转换空字符串为 None
    event_type_id_int = int(event_type_id) if event_type_id and event_type_id.strip() else None
    event_level_int = int(event_level) if event_level and event_level.strip() else None
    page_int = int(page) if page and page.strip() else 1
    page_size_int = int(page_size) if page_size and page_size.strip() else 20

    result = await event_service.get_events(
        db, user_id=current_user.id,
        device_sn=device_sn, baby_id=baby_id,
        event_type_id=event_type_id_int, event_level=event_level_int,
        page=page_int, page_size=page_size_int,
    )
    return success(data=result)


@router.get("/events/{event_id}", response_model=ApiResponse, summary="查询事件详情 [共用接口]")
async def get_event_detail(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """根据ID获取监测事件详细信息"""
    result = await event_service.get_event_detail(db, user_id=current_user.id, event_id=event_id)
    return success(data=result)


@router.post("/events/confirm", response_model=ApiResponse, summary="确认/标记事件 [共用接口]")
async def confirm_event(
    body: EventConfirm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """确认监测事件"""
    result = await event_service.confirm_event(db, event_id=body.event_id, parent_handled=body.parent_handled)
    return success(data=result, message="确认成功")


@router.get("/data", response_model=ApiResponse, summary="查询传感器数据 [共用接口]")
async def get_sensor_data(
    device_sn: str = Query(..., description="设备序列号"),
    start_time: str | None = Query(None, description="开始时间"),
    end_time: str | None = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """查询传感器历史数据"""
    start_dt = datetime.fromisoformat(start_time) if start_time else None
    end_dt = datetime.fromisoformat(end_time) if end_time else None
    result = await sensor_service.get_sensor_data(
        db, device_sn=device_sn, start_time=start_dt, end_time=end_dt,
        page=page, page_size=page_size,
    )
    return success(data=result)


# ==================== 小程序接口（需要用户认证） ====================

@router.get("/status/baby", response_model=ApiResponse, summary="获取宝宝状态及风险等级 [小程序接口]")
async def get_baby_status(
    device_sn: str = Query(..., description="设备序列号"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取宝宝当前状态及风险等级（硬件端已判断的结果）

    返回内容：
    - status_type: 五类状态 (sleeping/awake/playing/crying/danger)
    - status_level: 风险等级 (0-3)
    - risk_label: 中文风险标签 (正常/关注/警告/危险)
    - sensor_snapshot: 附带原始数据
    """
    result = await sensor_service.get_baby_status(db, device_sn=device_sn)
    return success(data=result)


# ========== 多模态融合监测 (2.1) ==========
@router.post("/fusion", response_model=ApiResponse, summary="多模态数据融合分析 [小程序接口]")
async def sensor_fusion(
    body: SensorFusionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """融合视频、雷达、音频数据进行综合分析，准确率>90%"""
    result = await sensor_service.sensor_fusion(
        db, device_sn=body.device_sn, baby_id=body.baby_id,
        video_data=body.video_data, radar_data=body.radar_data, audio_data=body.audio_data,
    )
    return success(data=result)


# ========== 五类场景分级响应 (2.2) ==========
@router.get("/scene/classify", response_model=ApiResponse, summary="场景分类识别 [小程序接口]")
async def classify_scene(
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """识别五类场景：熟睡/刚醒/高兴玩耍/哭闹/危险动作"""
    result = await sensor_service.classify_scene(db, baby_id=baby_id)
    return success(data=result)


@router.post("/scene/response", response_model=ApiResponse, summary="执行场景响应 [小程序接口]")
async def execute_scene_response(
    body: SceneResponseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """执行场景对应的响应脚本（灯光+声音+屏幕+推送）"""
    result = await sensor_service.execute_scene_response(
        db, baby_id=body.baby_id, scene_type=body.scene_type, response_mode=body.response_mode,
    )
    return success(data=result)