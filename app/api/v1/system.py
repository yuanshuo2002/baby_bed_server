"""
系统管理路由
包含硬件端数据上报接口
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.api.deps import get_db_session
from app.core.response import success
from app.models.device import Device
from app.schemas.base import ApiResponse
from app.schemas.system import PerformanceUpload, HealthUpload, SyncUploadRequest

router = APIRouter(prefix="/system", tags=["系统管理"])


# ==================== 硬件端上报接口（无需用户认证） ====================

@router.post("/performance/upload", response_model=ApiResponse, summary="性能数据上报 [硬件接口]")
async def upload_performance(
    body: PerformanceUpload,
    db: AsyncSession = Depends(get_db_session),
):
    """硬件端上报系统性能数据（CPU/内存/存储等）
    用于云端监控设备运行状态和性能趋势分析
    """
    # 更新设备在线状态
    result = await db.execute(select(Device).where(Device.device_sn == body.device_sn))
    device = result.scalar_one_or_none()
    if device:
        device.last_online_at = datetime.now()
        device.online_status = 1

    return success(data={
        "device_sn": body.device_sn,
        "status": "accepted",
        "record_id": None,
        "message": "性能数据接收成功",
    })


@router.post("/health/upload", response_model=ApiResponse, summary="健康状态上报 [硬件接口]")
async def upload_health(
    body: HealthUpload,
    db: AsyncSession = Depends(get_db_session),
):
    """硬件端上报系统健康状态（EMC/安全认证等）
    用于云端监控设备健康状态和安全合规
    """
    # 更新设备在线状态
    result = await db.execute(select(Device).where(Device.device_sn == body.device_sn))
    device = result.scalar_one_or_none()
    if device:
        device.last_online_at = datetime.now()
        device.online_status = 1

    return success(data={
        "device_sn": body.device_sn,
        "status": "accepted",
        "record_id": None,
        "message": "健康状态接收成功",
    })


@router.post("/sync/upload", response_model=ApiResponse, summary="数据同步上传 [硬件接口]")
async def upload_sync_data(
    body: SyncUploadRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """硬件端上传本地数据到云端进行同步备份
    支持批量上传传感器数据、事件记录、状态日志等
    """
    # 生成同步批次ID
    sync_id = body.sync_id or str(uuid.uuid4())

    # 统计处理结果
    records_processed = 0
    records_failed = 0
    errors = []

    # 更新设备在线状态
    result = await db.execute(select(Device).where(Device.device_sn == body.device_sn))
    device = result.scalar_one_or_none()
    if device:
        device.last_online_at = datetime.now()
        device.online_status = 1

    # TODO: 根据 records 中的 data_type 分别处理传感器数据、事件记录、状态日志
    for record in body.records:
        data_type = record.data_type
        data_items = record.data
        for item in data_items:
            try:
                # 这里可以根据 data_type 执行不同的存储逻辑
                # 目前暂时只做计数
                records_processed += 1
            except Exception as e:
                records_failed += 1
                errors.append({
                    "data_type": data_type,
                    "error": str(e),
                })

    return success(data={
        "device_sn": body.device_sn,
        "sync_id": sync_id,
        "status": "completed" if records_failed == 0 else "partial",
        "records_processed": records_processed,
        "records_failed": records_failed,
        "errors": errors,
    })