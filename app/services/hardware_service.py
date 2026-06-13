"""
硬件交互业务逻辑层

接口分类说明：
- 硬件接口（hardware_only）：仅硬件设备调用，无需用户认证
- 小程序接口：仅小程序端调用，需要用户认证
- 共用接口：硬件和小程序两端均可调用
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.screen_animation import ScreenAnimation
from app.models.ambient_light import AmbientLightConfig
from app.models.alarm_level import AlarmLevel


class HardwareService:
    """硬件交互服务"""

    # ==================== 硬件接口方法 ====================

    @staticmethod
    async def get_animation_list_by_device(db: AsyncSession, device_sn: str) -> list[dict]:
        """获取设备的屏幕动画列表（硬件端调用）"""
        query = select(ScreenAnimation).where(ScreenAnimation.is_active == 1)
        result = await db.execute(query)
        animations = result.scalars().all()
        return [
            {
                "id": a.id,
                "event_type_id": a.event_type_id,
                "animation_name": a.animation_name,
                "animation_desc": a.animation_desc,
                "animation_url": a.animation_url,
                "duration_ms": a.duration_ms,
                "file_size_bytes": a.file_size_bytes,
                "screen_mode": a.screen_mode,
                "bg_color": a.bg_color,
                "text_overlay": a.text_overlay,
            }
            for a in animations
        ]

    @staticmethod
    async def get_light_configs_by_device(db: AsyncSession, device_sn: str) -> list[dict]:
        """获取设备的环境灯配置列表（硬件端调用）"""
        query = select(AmbientLightConfig).where(AmbientLightConfig.is_active == 1)
        result = await db.execute(query)
        configs = result.scalars().all()
        return [
            {
                "id": c.id,
                "event_type_id": c.event_type_id,
                "alarm_level_id": c.alarm_level_id,
                "light_mode": c.light_mode,
                "color_primary": c.color_primary,
                "color_secondary": c.color_secondary,
                "brightness_pct": c.brightness_pct,
                "blink_enabled": c.blink_enabled,
                "blink_freq_hz": float(c.blink_freq_hz) if c.blink_freq_hz else None,
                "gradient_enabled": c.gradient_enabled,
                "gradient_ms": c.gradient_ms,
                "duration_sec": c.duration_sec,
            }
            for c in configs
        ]

    # ==================== 小程序接口方法 ====================

    @staticmethod
    async def get_animation_list(db: AsyncSession, event_type_id: int | None = None) -> list[dict]:
        """获取屏幕动画列表（小程序端调用）"""
        query = select(ScreenAnimation).where(ScreenAnimation.is_active == 1)
        if event_type_id:
            query = query.where(ScreenAnimation.event_type_id == event_type_id)

        result = await db.execute(query)
        animations = result.scalars().all()
        return [
            {
                "id": a.id,
                "event_type_id": a.event_type_id,
                "animation_name": a.animation_name,
                "animation_desc": a.animation_desc,
                "animation_url": a.animation_url,
                "duration_ms": a.duration_ms,
                "file_size_bytes": a.file_size_bytes,
                "screen_mode": a.screen_mode,
                "bg_color": a.bg_color,
                "text_overlay": a.text_overlay,
            }
            for a in animations
        ]

    @staticmethod
    async def get_light_configs(db: AsyncSession, event_type_id: int | None = None) -> list[dict]:
        """获取灯语配置列表（小程序端调用）"""
        query = select(AmbientLightConfig).where(AmbientLightConfig.is_active == 1)
        if event_type_id:
            query = query.where(AmbientLightConfig.event_type_id == event_type_id)

        result = await db.execute(query)
        configs = result.scalars().all()
        return [
            {
                "id": c.id,
                "event_type_id": c.event_type_id,
                "alarm_level_id": c.alarm_level_id,
                "light_mode": c.light_mode,
                "color_primary": c.color_primary,
                "color_secondary": c.color_secondary,
                "brightness_pct": c.brightness_pct,
                "blink_enabled": c.blink_enabled,
                "blink_freq_hz": float(c.blink_freq_hz) if c.blink_freq_hz else None,
                "gradient_enabled": c.gradient_enabled,
                "gradient_ms": c.gradient_ms,
                "duration_sec": c.duration_sec,
            }
            for c in configs
        ]

    @staticmethod
    async def save_light_config(db: AsyncSession, event_type_id: int, alarm_level_id: int | None, **kwargs) -> dict:
        """保存灯语配置（小程序端调用）"""
        config = AmbientLightConfig(
            event_type_id=event_type_id,
            alarm_level_id=alarm_level_id,
            **kwargs,
        )
        db.add(config)
        await db.flush()
        return {"id": config.id, "message": "配置保存成功"}

    @staticmethod
    async def get_alarm_levels(db: AsyncSession) -> list[dict]:
        """获取告警级别列表（小程序端调用）"""
        result = await db.execute(select(AlarmLevel).order_by(AlarmLevel.sort_order))
        levels = result.scalars().all()
        return [
            {
                "id": l.id,
                "level_code": l.level_code,
                "level_name": l.level_name,
                "level_value": l.level_value,
                "screen_behavior": l.screen_behavior,
                "sound_behavior": l.sound_behavior,
                "app_behavior": l.app_behavior,
                "push_enabled": l.push_enabled,
                "push_vibrate": l.push_vibrate,
                "push_sound_max": l.push_sound_max,
                "auto_call": l.auto_call,
                "auto_record": l.auto_record,
                "record_before_sec": l.record_before_sec,
            }
            for l in levels
        ]

    # ==================== 共用方法 ====================

    # ========== 氛围灯语与UI联动 (4.2) ==========
    @staticmethod
    async def control_light(device_sn: str, color_r: int, color_g: int, color_b: int, brightness: int, animation_mode: str = "static") -> dict:
        """控制氛围灯（硬件端调用）"""
        # TODO: 发送指令到设备，要求渐变无卡顿
        return {
            "device_sn": device_sn,
            "color": f"#{color_r:02x}{color_g:02x}{color_b:02x}",
            "brightness": brightness,
            "animation_mode": animation_mode,
            "transition_ms": 500,  # 渐变时间
            "status": "success",
            "message": "灯语控制指令已发送",
        }

    @staticmethod
    async def control_screen_animation(device_sn: str, animation_id: int | None = None, animation_name: str | None = None) -> dict:
        """控制屏幕动画（硬件端调用）"""
        # TODO: 发送指令到设备，要求加载<1s
        return {
            "device_sn": device_sn,
            "animation_id": animation_id,
            "animation_name": animation_name or "default",
            "load_time_ms": 800,  # 要求<1000ms
            "status": "playing",
            "message": "屏幕动画已加载",
        }

    # ========== 硬件模式切换 (4.3) ==========
    @staticmethod
    async def switch_device_mode(device_sn: str, mode: str, baby_id: int | None = None) -> dict:
        """切换设备工作模式（共用接口）"""
        # 模式: sleep_bed(睡床)/play_bed(游戏床)/side_bed(拼床)
        mode_configs = {
            "sleep_bed": {
                "monitor_enabled": True,
                "alert_enabled": True,
                "light_enabled": True,
                "sound_enabled": True,
            },
            "play_bed": {
                "monitor_enabled": True,
                "alert_enabled": False,  # 游戏模式关闭警报
                "light_enabled": True,
                "sound_enabled": False,
            },
            "side_bed": {
                "monitor_enabled": True,
                "alert_enabled": True,
                "light_enabled": False,
                "sound_enabled": False,
            },
        }
        config = mode_configs.get(mode, mode_configs["sleep_bed"])

        return {
            "device_sn": device_sn,
            "mode": mode,
            "config": config,
            "status": "success",
            "message": f"已切换至{mode}模式",
        }

    @staticmethod
    async def get_device_mode(device_sn: str) -> dict:
        """获取设备当前模式（共用接口）"""
        return {
            "device_sn": device_sn,
            "current_mode": "sleep_bed",
            "mode_since": "2024-01-15T08:00:00",
            "config": {
                "monitor_enabled": True,
                "alert_enabled": True,
            },
        }

    # ==================== 动画管理方法（小程序端） ====================

    @staticmethod
    async def create_animation(db: AsyncSession, animation_data: dict) -> dict:
        """创建动画配置（小程序端调用）"""
        animation = ScreenAnimation(**animation_data)
        db.add(animation)
        await db.flush()
        await db.refresh(animation)
        return {
            "id": animation.id,
            "message": "动画创建成功",
        }

    @staticmethod
    async def update_animation(db: AsyncSession, animation_id: int, update_data: dict) -> dict:
        """更新动画配置（小程序端调用）"""
        result = await db.execute(
            select(ScreenAnimation).where(ScreenAnimation.id == animation_id)
        )
        animation = result.scalar_one_or_none()
        if not animation:
            return {"success": False, "message": "动画不存在"}

        for key, value in update_data.items():
            if value is not None and hasattr(animation, key):
                setattr(animation, key, value)

        await db.flush()
        return {"success": True, "message": "动画更新成功"}

    @staticmethod
    async def delete_animation(db: AsyncSession, animation_id: int) -> dict:
        """删除动画配置（小程序端调用）"""
        result = await db.execute(
            select(ScreenAnimation).where(ScreenAnimation.id == animation_id)
        )
        animation = result.scalar_one_or_none()
        if not animation:
            return {"success": False, "message": "动画不存在"}

        await db.delete(animation)
        await db.flush()
        return {"success": True, "message": "动画删除成功"}

    @staticmethod
    async def get_animation_detail(db: AsyncSession, animation_id: int) -> dict | None:
        """获取动画详情（小程序端调用）"""
        result = await db.execute(
            select(ScreenAnimation).where(ScreenAnimation.id == animation_id)
        )
        animation = result.scalar_one_or_none()
        if not animation:
            return None

        return {
            "id": animation.id,
            "event_type_id": animation.event_type_id,
            "animation_name": animation.animation_name,
            "animation_desc": animation.animation_desc,
            "animation_url": animation.animation_url,
            "duration_ms": animation.duration_ms,
            "file_size_bytes": animation.file_size_bytes,
            "screen_mode": animation.screen_mode,
            "bg_color": animation.bg_color,
            "text_overlay": animation.text_overlay,
            "is_active": animation.is_active,
            "created_at": animation.created_at.isoformat() if animation.created_at else None,
        }


hardware_service = HardwareService()
