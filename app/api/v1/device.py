"""
设备管理路由
包含设备注册、模式切换、状态查询等接口

接口分类说明：
- 硬件接口（hardware_only）：仅硬件设备调用，无需用户认证
- 小程序接口：仅小程序端调用，需要用户认证
- 共用接口：硬件和小程序两端均可调用
"""
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.device import DeviceRegister, DeviceBind, DeviceModeSwitch, ThemeConfig, ThemeConfigResponse, UpdateDeviceName
from app.services.device_service import device_service

router = APIRouter(prefix="/device", tags=["设备管理"])


# ==================== 硬件接口（无需用户认证） ====================

@router.post("/register", response_model=ApiResponse, summary="注册设备 [硬件接口]")
async def register_device(
    body: DeviceRegister,
    db: AsyncSession = Depends(get_db_session),
):
    """注册新设备到系统中（硬件端调用）"""
    result = await device_service.register_device(
        db, device_sn=body.device_sn, device_name=body.device_name, device_model=body.device_model,
    )
    return success(data=result, message="设备注册成功")


# ==================== 共用接口（硬件和小程序均可用） ====================


@router.post("/bind", response_model=ApiResponse, summary="绑定设备到宝宝 [共用接口]")
async def bind_device(
    body: DeviceBind,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """将设备绑定到指定宝宝"""
    result = await device_service.bind_device(db, user_id=current_user.id, device_sn=body.device_sn, baby_id=body.baby_id)
    return success(data=result, message="设备绑定成功")


@router.post("/unbind", response_model=ApiResponse, summary="解绑设备 [共用接口]")
async def unbind_device(
    device_sn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """解除设备与宝宝的绑定"""
    result = await device_service.unbind_device(db, user_id=current_user.id, device_sn=device_sn)
    return success(data=result, message="设备解绑成功")


@router.post("/mode/switch", response_model=ApiResponse, summary="切换设备模式 [共用接口]")
async def switch_device_mode(
    body: DeviceModeSwitch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """切换设备工作模式"""
    result = await device_service.switch_mode(
        db, user_id=current_user.id,
        device_sn=body.device_sn, target_mode=body.target_mode,
        switch_type=body.switch_type, switch_reason=None,
    )
    return success(data=result, message="模式切换成功")


@router.get("/mode/history", response_model=ApiResponse, summary="获取模式切换历史 [共用接口]")
async def get_mode_switch_history(
    device_sn: str = Query(..., description="设备序列号"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取设备模式切换历史记录"""
    result = await device_service.get_mode_history(db, user_id=current_user.id, device_sn=device_sn, page=page, page_size=page_size)
    return success(data=result)


# ==================== 小程序接口（需要用户认证） ====================


@router.get("/list", response_model=ApiResponse, summary="获取设备列表 [小程序接口]")
async def get_device_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前家庭下的所有设备列表"""
    result = await device_service.get_device_list(db, user_id=current_user.id)
    return success(data=result)


@router.get("/status/{device_sn}", response_model=ApiResponse, summary="查询设备状态 [小程序接口]")
async def get_device_status(
    device_sn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """查询指定设备的实时状态"""
    result = await device_service.get_device_status(db, user_id=current_user.id, device_sn=device_sn)
    return success(data=result)


@router.get("/firmware/version", response_model=ApiResponse, summary="获取固件版本")
async def get_firmware_version(device_sn: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return success(data=await device_service.get_firmware_version(db, current_user.id, device_sn))


@router.get("/battery", response_model=ApiResponse, summary="获取电池状态")
async def get_battery(device_sn: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return success(data=await device_service.get_battery(db, current_user.id, device_sn))


@router.post("/{device_sn}/diagnose", response_model=ApiResponse, summary="设备诊断")
async def diagnose_device(device_sn: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return success(data=await device_service.diagnose(db, current_user.id, device_sn))


@router.post("/{device_sn}/reboot", response_model=ApiResponse, summary="远程重启")
async def reboot_device(device_sn: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    return success(data=await device_service.reboot(db, current_user.id, device_sn))


@router.delete("/{device_sn}", response_model=ApiResponse, summary="注销设备")
async def delete_device(device_sn: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await device_service.delete_device(db, current_user.id, device_sn)
    return success(message="设备已注销")

@router.put("/name", response_model=ApiResponse, summary="更新设备名称 [小程序接口]")
async def update_device_name(
    body: UpdateDeviceName,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """更新设备名称"""
    result = await device_service.update_device_name(
        db, user_id=current_user.id,
        device_sn=body.device_sn, new_name=body.device_name,
    )
    return success(data=result, message="设备名称更新成功")
