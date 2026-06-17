"""
硬件交互路由
包含心跳和模式切换接口

接口分类说明：
- 硬件接口（hardware_only）：仅硬件设备调用，无需用户认证
- 共用接口：硬件和小程序两端均可调用
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.api.deps import get_db_session
from app.core.response import success
from app.models.device import Device, VALID_WORK_MODES
from app.models.baby import Baby
from app.schemas.base import ApiResponse
from app.services.hardware_service import hardware_service

router = APIRouter(prefix="/hardware", tags=["硬件交互"])


# ==================== 硬件接口（无需用户认证） ====================

@router.post("/heartbeat", response_model=ApiResponse, summary="设备心跳 [硬件接口]")
async def device_heartbeat(
    device_sn: str = Query(..., description="设备序列号"),
    work_mode: str | None = Query(None, description=f"当前工作模式: {VALID_WORK_MODES}"),
    online_status: int = Query(1, description="在线状态: 1=在线, 0=离线"),
    cpu_percent: float | None = Query(None, description="CPU使用率(%)"),
    memory_percent: float | None = Query(None, description="内存使用率(%)"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    设备心跳接口（硬件端调用，无需用户认证）
    硬件端定期发送心跳，后端返回设备绑定状态 baby_id
    用于硬件端获取当前绑定的 baby_id 和设备状态

    work_mode 可选值: sleep(睡眠模式), play(游戏模式), co_sleep(拼床模式)
    """
    # 查询设备
    result = await db.execute(select(Device).where(Device.device_sn == device_sn))
    device = result.scalar_one_or_none()

    if not device:
        return success(data={
            "device_sn": device_sn,
            "is_bound": False,
            "baby_id": None,
            "family_id": None,
            "work_mode": work_mode,
            "online_status": 0,
            "last_bind_at": None,
        })

    # 更新设备状态
    device.last_online_at = datetime.now()
    device.online_status = online_status

    # 校验 work_mode 枚举值
    if work_mode:
        if work_mode not in VALID_WORK_MODES:
            return success(data={
                "device_sn": device_sn,
                "is_bound": device.baby_id is not None,
                "baby_id": device.baby_id,
                "family_id": None,
                "work_mode": device.work_mode,
                "online_status": online_status,
                "last_bind_at": device.updated_at.isoformat() if device.updated_at else None,
                "error": f"无效的work_mode: {work_mode}, 可选值: {VALID_WORK_MODES}",
            })
        device.work_mode = work_mode

    # 查询绑定状态
    # 设备绑定到 family 表示已绑定（baby_id 可选）
    family_id = device.family_id
    is_bound = family_id is not None

    # 兼容旧逻辑：如果有 baby_id 则返回
    baby_id = device.baby_id

    return success(data={
        "device_sn": device_sn,
        "is_bound": is_bound,
        "baby_id": baby_id,
        "family_id": family_id,
        "work_mode": device.work_mode,
        "online_status": online_status,
        "last_bind_at": device.updated_at.isoformat() if device.updated_at else None,
    })


# ==================== 共用接口（硬件和小程序均可用） ====================

@router.post("/mode/switch", response_model=ApiResponse, summary="切换设备工作模式 [共用接口]")
async def switch_device_mode(
    device_sn: str,
    mode: str = Query(..., description=f"模式: {VALID_WORK_MODES}"),
    baby_id: int | None = Query(None, description="宝宝ID"),
    db: AsyncSession = Depends(get_db_session),
):
    """切换婴儿床工作模式，不同模式下看护策略自动调整

    mode 可选值: sleep(睡眠模式), play(游戏模式), co_sleep(拼床模式)
    """
    if mode not in VALID_WORK_MODES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "message": f"无效的工作模式: {mode}, 可选值: {list(VALID_WORK_MODES)}",
                "data": None,
            }
        )
    result = await hardware_service.switch_device_mode(device_sn=device_sn, mode=mode, baby_id=baby_id)
    return success(data=result, message="模式切换成功")


@router.get("/mode/current", response_model=ApiResponse, summary="获取当前工作模式 [共用接口]")
async def get_device_mode(
    device_sn: str,
    db: AsyncSession = Depends(get_db_session),
):
    """获取设备当前工作模式及配置

    返回工作模式: sleep(睡眠模式), play(游戏模式), co_sleep(拼床模式)
    """
    result = await hardware_service.get_device_mode(device_sn=device_sn)
    return success(data=result)