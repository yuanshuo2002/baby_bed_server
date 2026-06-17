"""
设备管理业务逻辑层
"""
from datetime import datetime, timedelta
from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException, BusinessException
from app.models.device import Device, VALID_WORK_MODES
from app.models.device_mode import DeviceModeSwitch
from app.services.family_service import FamilyService


class DeviceService:
    """设备管理服务"""

    @staticmethod
    async def _get_family_device(db: AsyncSession, user_id: int, device_sn: str) -> Device:
        """获取属于用户家庭的设备（内部方法）"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(
            select(Device).where(
                Device.device_sn == device_sn, Device.family_id == family.id,
            )
        )
        device = result.scalar_one_or_none()
        if not device:
            raise ForbiddenException("设备不属于当前家庭")
        return device

    @staticmethod
    async def _get_device_for_user(db: AsyncSession, user_id: int, device_sn: str) -> Device:
        """获取属于用户家庭的设备
        - 设备不存在 → NotFoundException
        - 设备未绑定到家庭 → ForbiddenException
        - 设备不属于用户家庭 → ForbiddenException
        """
        result = await db.execute(select(Device).where(Device.device_sn == device_sn))
        device = result.scalar_one_or_none()

        if not device:
            raise NotFoundException("设备不存在")

        if device.family_id is None:
            raise ForbiddenException("设备未绑定到任何家庭")

        family = await FamilyService._get_user_family_obj(db, user_id)
        if device.family_id != family.id:
            raise ForbiddenException("设备不属于当前家庭")
        return device

    @staticmethod
    async def register_device(db: AsyncSession, device_sn: str, device_name: str, device_model: str | None = None) -> dict:
        """注册设备（硬件端调用，无需用户认证）"""
        result = await db.execute(select(Device).where(Device.device_sn == device_sn))
        if result.scalar_one_or_none():
            raise ConflictException("设备序列号已注册")

        device = Device(device_sn=device_sn, device_name=device_name, device_model=device_model)
        db.add(device)
        await db.flush()

        return {"id": device.id, "device_sn": device.device_sn, "device_name": device.device_name}

    @staticmethod
    async def bind_device(db: AsyncSession, user_id: int, device_sn: str, baby_id: int | None = None) -> dict:
        """绑定设备到家庭（baby_id可选）"""
        result = await db.execute(select(Device).where(Device.device_sn == device_sn))
        device = result.scalar_one_or_none()

        # 设备未注册：先注册设备
        if not device:
            device = Device(device_sn=device_sn, device_name=None, device_model=None)
            db.add(device)
            await db.flush()

        family = await FamilyService._get_user_family_obj(db, user_id)

        # 设备已绑定到其他家庭
        if device.family_id is not None and device.family_id != family.id:
            raise ForbiddenException("设备已被其他家庭绑定")

        # 如果提供了 baby_id，验证宝宝属于当前家庭
        if baby_id is not None:
            from app.models.baby import Baby
            baby = await db.execute(select(Baby).where(Baby.id == baby_id, Baby.family_id == family.id))
            if not baby.scalar_one_or_none():
                raise ForbiddenException("宝宝不属于当前家庭")
            device.baby_id = baby_id

        device.family_id = family.id
        device.last_online_at = datetime.now()
        return {"device_sn": device_sn, "baby_id": device.baby_id, "message": "绑定成功"}

    @staticmethod
    async def bind_baby_to_device(db: AsyncSession, user_id: int, device_sn: str, baby_id: int) -> dict:
        """将宝宝绑定到已归属家庭的设备"""
        device = await DeviceService._get_family_device(db, user_id, device_sn)
        from app.models.baby import Baby
        baby = await db.execute(select(Baby).where(Baby.id == baby_id, Baby.family_id == device.family_id))
        baby_obj = baby.scalar_one_or_none()
        if not baby_obj:
            raise ForbiddenException("宝宝不属于当前家庭")

        device.baby_id = baby_id
        return {"device_sn": device_sn, "baby_id": baby_id, "message": "宝宝绑定成功"}

    @staticmethod
    async def unbind_device(db: AsyncSession, user_id: int, device_sn: str) -> dict:
        """解绑设备"""
        device = await DeviceService._get_family_device(db, user_id, device_sn)

        device.baby_id = None
        return {"device_sn": device_sn, "message": "解绑成功"}

    @staticmethod
    async def get_device_list(db: AsyncSession, user_id: int) -> list[dict]:
        """获取设备列表（返回当前家庭下的所有设备）"""
        family = await FamilyService._get_user_family_obj(db, user_id)

        # 查询设备：基于 family_id 查询
        result = await db.execute(
            select(Device).where(Device.family_id == family.id)
        )
        devices = result.scalars().all()
        return [
            {
                "id": d.id,
                "device_sn": d.device_sn,
                "baby_id": d.baby_id,
                "device_name": d.device_name,
                "device_model": d.device_model,
                "firmware_version": d.firmware_version,
                "work_mode": d.work_mode,
                "online_status": d.online_status,
                "last_online_at": d.last_online_at.isoformat() if d.last_online_at else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in devices
        ]

    @staticmethod
    async def get_device_status(db: AsyncSession, user_id: int, device_sn: str) -> dict:
        """查询设备状态（支持未绑定设备）"""
        device = await DeviceService._get_device_for_user(db, user_id, device_sn)
        return {
            "device_sn": device.device_sn,
            "online_status": device.online_status,
            "work_mode": device.work_mode,
            "last_online_at": device.last_online_at.isoformat() if device.last_online_at else None,
        }

    @staticmethod
    async def switch_mode(
        db: AsyncSession, user_id: int, device_sn: str,
        target_mode: str, switch_type: str = "manual", switch_reason: str | None = None,
    ) -> dict:
        """切换设备模式

        Args:
            target_mode: 目标模式，可选值: sleep, play, co_sleep
        """
        if target_mode not in VALID_WORK_MODES:
            raise BusinessException(f"无效的工作模式: {target_mode}, 可选值: {list(VALID_WORK_MODES)}")

        device = await DeviceService._get_family_device(db, user_id, device_sn)

        from_mode = device.work_mode
        device.work_mode = target_mode

        # 记录切换历史
        switch_record = DeviceModeSwitch(
            device_sn=device.device_sn,
            baby_id=device.baby_id or 0,
            from_mode=from_mode,
            to_mode=target_mode,
            switch_type=switch_type,
            switch_reason=switch_reason,
        )
        db.add(switch_record)

        return {"device_sn": device_sn, "from_mode": from_mode, "to_mode": target_mode}

    @staticmethod
    async def get_mode_history(db: AsyncSession, user_id: int, device_sn: str, page: int = 1, page_size: int = 20) -> dict:
        """获取模式切换历史"""
        device = await DeviceService._get_family_device(db, user_id, device_sn)

        query = select(DeviceModeSwitch).where(DeviceModeSwitch.device_sn == device.device_sn).order_by(desc(DeviceModeSwitch.switched_at))
        # 简单分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        records = result.scalars().all()

        return {
            "items": [
                {
                    "id": r.id,
                    "device_sn": r.device_sn,
                    "baby_id": r.baby_id,
                    "from_mode": r.from_mode,
                    "to_mode": r.to_mode,
                    "switch_type": r.switch_type,
                    "switch_reason": r.switch_reason,
                    "switched_at": r.switched_at.isoformat() if r.switched_at else None,
                }
                for r in records
            ],
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def get_firmware_version(db: AsyncSession, user_id: int, device_sn: str) -> dict:
        device = await DeviceService._get_family_device(db, user_id, device_sn)
        return {"device_sn": device_sn, "firmware_version": device.firmware_version}

    @staticmethod
    async def get_battery(db: AsyncSession, user_id: int, device_sn: str) -> dict:
        await DeviceService._get_family_device(db, user_id, device_sn)
        return {"device_sn": device_sn, "battery_pct": None, "charging": None, "status": "not_reported"}

    @staticmethod
    async def diagnose(db: AsyncSession, user_id: int, device_sn: str) -> dict:
        await DeviceService._get_family_device(db, user_id, device_sn)
        return {"device_sn": device_sn, "status": "accepted", "message": "诊断请求已受理，等待设备通信模块执行"}

    @staticmethod
    async def reboot(db: AsyncSession, user_id: int, device_sn: str) -> dict:
        await DeviceService._get_family_device(db, user_id, device_sn)
        return {"device_sn": device_sn, "status": "accepted", "message": "重启请求已受理，等待设备通信模块执行"}

    @staticmethod
    async def delete_device(db: AsyncSession, user_id: int, device_sn: str) -> None:
        """注销设备：删除设备及所有关联数据
        - 设备不存在 → 404
        - 设备已绑定(baby_id不为null) →提示先解绑
        - 设备未绑定(baby_id为null) → 清理数据并删除
        """
        result = await db.execute(select(Device).where(Device.device_sn == device_sn))
        device = result.scalar_one_or_none()

        if not device:
            raise NotFoundException("设备不存在")

        if device.baby_id is not None:
            raise ConflictException("请先解绑设备后再删除")

        # 设备未绑定，清理关联数据（按照数据模型关系文档的清理顺序）
        from sqlalchemy import delete
        from app.models.video import Video
        from app.models.sensor import SensorDataRaw
        from app.models.status_log import BabyStatusLog
        from app.models.cry_event import CryEvent
        from app.models.danger_event import DangerEvent

        # 1. 清理视频记录
        await db.execute(delete(Video).where(Video.device_sn == device_sn))

        # 2. 清理传感器数据
        await db.execute(delete(SensorDataRaw).where(SensorDataRaw.device_sn == device_sn))

        # 3. 清理状态日志
        await db.execute(delete(BabyStatusLog).where(BabyStatusLog.device_sn == device_sn))

        # 4. 删除设备记录
        await db.delete(device)
        await db.flush()

    @staticmethod
    async def cleanup_offline_devices(db: AsyncSession, timeout_minutes: int = 5) -> dict:
        """清理离线设备，将超过指定时间未上线的设备设为离线状态"""
        timeout = datetime.now() - timedelta(minutes=timeout_minutes)

        # 查询即将被设为离线的设备
        query = select(Device).where(
            Device.online_status == 1,
            Device.last_online_at < timeout,
        )
        result = await db.execute(query)
        offline_devices = result.scalars().all()
        count = len(offline_devices)

        if count > 0:
            # 批量更新为离线
            await db.execute(
                update(Device)
                .where(Device.online_status == 1)
                .where(Device.last_online_at < timeout)
                .values(online_status=0)
            )
            await db.flush()

        return {
            "cleaned_count": count,
            "timeout_minutes": timeout_minutes,
            "device_sns": [d.device_sn for d in offline_devices],
        }

    @staticmethod
    async def update_device_online_status(db: AsyncSession, device_sn: str) -> bool:
        """更新设备在线状态（心跳时调用）"""
        result = await db.execute(select(Device).where(Device.device_sn == device_sn))
        device = result.scalar_one_or_none()
        if not device:
            return False

        device.online_status = 1
        device.last_online_at = datetime.now()
        await db.flush()
        return True

    @staticmethod
    async def update_device_name(db: AsyncSession, user_id: int, device_sn: str, new_name: str) -> dict:
        """更新设备名称
        - 设备不存在 → 404
        - 已绑定设备(baby_id不为null) → 校验家庭归属后更新
        - 未绑定设备(baby_id为null) → 直接更新
        """
        # 获取设备（支持未绑定设备）
        result = await db.execute(select(Device).where(Device.device_sn == device_sn))
        device = result.scalar_one_or_none()
        if not device:
            raise NotFoundException("设备不存在")

        # 已绑定设备校验家庭归属
        if device.baby_id is not None:
            family = await FamilyService._get_user_family_obj(db, user_id)
            from app.models.baby import Baby
            result = await db.execute(
                select(Device).join(Baby, Device.baby_id == Baby.id).where(
                    Device.device_sn == device_sn, Baby.family_id == family.id,
                )
            )
            bound_device = result.scalar_one_or_none()
            if not bound_device:
                raise ForbiddenException("设备不属于当前家庭")

        device.device_name = new_name
        await db.flush()
        return {"device_sn": device_sn, "device_name": new_name, "message": "设备名称更新成功"}


device_service = DeviceService()