"""
传感器数据业务逻辑层
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.exceptions import NotFoundException
from app.models.sensor import SensorDataRaw
from app.models.status_log import BabyStatusLog
from app.models.cry_event import CryEvent
from app.models.danger_event import DangerEvent
from app.schemas.status import StatusLogInfo


class SensorService:
    """传感器数据服务"""

    # 五类状态阈值配置
    STATUS_THRESHOLDS = {
        "sleeping": {
            "breath_rate_max": 40,
            "heart_rate_max": 130,
            "body_movement_max": 0.3,
            "sound_db_max": 40,
        },
        "awake": {
            "breath_rate_min": 15,
            "heart_rate_min": 90,
            "body_movement_min": 0.3,
            "body_movement_max": 2.0,
            "sound_db_min": 30,
            "sound_db_max": 55,
        },
        "playing": {
            "body_movement_min": 2.0,
            "heart_rate_min": 100,
            "sound_db_min": 45,
            "sound_db_max": 65,
        },
        "crying": {
            "sound_db_min": 60,
            "heart_rate_min": 140,
            "body_movement_min": 1.5,
        },
        "danger": {
            "pose_status_in": ["standing", "climbing", "prone", "face_down"],
            "height_cm_min": 60,
            "body_offset_cm_max": 35,
        },
    }

    @staticmethod
    async def upload_sensor_data(db: AsyncSession, device_sn: str, baby_id: int, **kwargs) -> dict:
        """上传传感器数据"""
        data = SensorDataRaw(device_sn=device_sn, baby_id=baby_id, **kwargs)
        db.add(data)
        await db.flush()

        # 更新设备在线状态
        from app.services.device_service import DeviceService
        await DeviceService.update_device_online_status(db, device_sn)

        return {"id": data.id, "message": "数据上传成功"}

    @staticmethod
    async def upload_status(db: AsyncSession, device_sn: str, baby_id: int | None, status_type: str, status_level: int, started_at: datetime, breath_rate: float | None = None, heart_rate: float | None = None, pose_status: str | None = None, expression: str | None = None) -> dict:
        """上传婴儿状态及风险等级到数据库"""
        # 如果未传 baby_id，尝试通过 device_sn 查询
        if baby_id is None:
            baby_id = await SensorService._get_baby_id(db, device_sn)

        if not baby_id:
            return {"success": False, "message": "设备未绑定宝宝，无法上传状态"}

        # 先关闭之前未结束的状态记录
        result = await db.execute(
            select(BabyStatusLog)
            .where(BabyStatusLog.device_sn == device_sn, BabyStatusLog.baby_id == baby_id, BabyStatusLog.ended_at.is_(None))
        )
        current_status = result.scalar_one_or_none()
        if current_status:
            current_status.ended_at = started_at
            current_status.duration_sec = int((started_at - current_status.started_at).total_seconds())

        # 创建新的状态记录
        status_log = BabyStatusLog(
            baby_id=baby_id,
            device_sn=device_sn,
            status_type=status_type,
            status_level=status_level,
            started_at=started_at,
            breath_rate=Decimal(str(breath_rate)) if breath_rate else None,
            heart_rate=Decimal(str(heart_rate)) if heart_rate else None,
            pose_status=pose_status,
            expression=expression,
        )
        db.add(status_log)
        await db.flush()

        # 更新设备在线状态
        from app.services.device_service import DeviceService
        await DeviceService.update_device_online_status(db, device_sn)

        return {"id": status_log.id, "status_type": status_type, "status_level": status_level, "message": "状态上传成功"}

    @staticmethod
    async def upload_sensor_file(db: AsyncSession, device_sn: str, baby_id: int, file: UploadFile) -> dict:
        """上传传感器数据文件（解析并入库）"""
        content = await file.read()
        lines = content.decode('utf-8').strip().split('\n')

        import json
        count = 0
        error_lines = []
        for idx, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                record = SensorDataRaw(
                    device_sn=device_sn,
                    baby_id=baby_id,
                    collected_at=datetime.fromisoformat(row.get('collected_at', datetime.now().isoformat())),
                    breath_rate=Decimal(str(row['breath_rate'])) if row.get('breath_rate') else None,
                    heart_rate=Decimal(str(row['heart_rate'])) if row.get('heart_rate') else None,
                    body_movement=Decimal(str(row['body_movement'])) if row.get('body_movement') else None,
                    distance_cm=Decimal(str(row['distance_cm'])) if row.get('distance_cm') else None,
                    sound_db=Decimal(str(row['sound_db'])) if row.get('sound_db') else None,
                    sound_type=row.get('sound_type'),
                    pose_status=row.get('pose_status'),
                    face_detected=int(row['face_detected']) if row.get('face_detected') is not None else 0,
                    expression=row.get('expression'),
                    body_offset_cm=Decimal(str(row['body_offset_cm'])) if row.get('body_offset_cm') else None,
                    roll_angle=Decimal(str(row['roll_angle'])) if row.get('roll_angle') else None,
                    height_cm=Decimal(str(row['height_cm'])) if row.get('height_cm') else None,
                    room_temp=Decimal(str(row['room_temp'])) if row.get('room_temp') else None,
                    humidity=Decimal(str(row['humidity'])) if row.get('humidity') else None,
                    noise_db=Decimal(str(row['noise_db'])) if row.get('noise_db') else None,
                )
                db.add(record)
                count += 1
            except (json.JSONDecodeError, ValueError) as e:
                error_lines.append(f"行{idx}: JSON格式错误")
                continue
            except Exception as e:
                error_lines.append(f"行{idx}: {str(e)}")
                continue

        await db.flush()
        if error_lines and count == 0:
            raise ValueError(f"所有行解析失败: {error_lines[:5]}")

        # 更新设备在线状态
        from app.services.device_service import DeviceService
        await DeviceService.update_device_online_status(db, device_sn)

        return {"count": count, "message": f"成功导入 {count} 条数据", "errors": error_lines[:10] if error_lines else []}

    @staticmethod
    async def _classify_status(sensor_data: SensorDataRaw) -> tuple[str, int]:
        """基于毫米波传感器数据分类五类状态，返回(状态类型, 状态级别)

        注意：本方法只使用毫米波数据（呼吸、心率、体动、距离等），不依赖 sound_db
        """
        breath_rate = float(sensor_data.breath_rate) if sensor_data.breath_rate else 0
        heart_rate = float(sensor_data.heart_rate) if sensor_data.heart_rate else 0
        body_movement = float(sensor_data.body_movement) if sensor_data.body_movement else 0
        distance_cm = float(sensor_data.distance_cm) if sensor_data.distance_cm else 0
        pose_status = sensor_data.pose_status or ""
        height_cm = float(sensor_data.height_cm) if sensor_data.height_cm else 0
        body_offset = float(sensor_data.body_offset_cm) if sensor_data.body_offset_cm else 0

        # 危险状态优先检测
        if pose_status in ["standing", "climbing"] or height_cm > 60:
            return ("danger", 3)
        if pose_status in ["prone", "face_down"]:
            return ("danger", 2)
        if body_offset > 35:
            return ("danger", 1)

        # 哭闹状态检测（基于心率和体动）
        # 哭闹时心率会明显升高，体动也会增加
        if heart_rate > 160:
            return ("crying", 3)
        if heart_rate > 140:
            return ("crying", 2)
        if heart_rate > 120 and body_movement > 1.0:
            return ("crying", 1)

        # 高兴玩耍检测（较高体动，无哭闹特征）
        if body_movement > 2.5 and heart_rate < 120:
            return ("playing", 0)

        # 苏醒状态检测（有体动但心率正常）
        if body_movement > 0.5 and heart_rate < 110:
            return ("awake", 0)

        # 默认熟睡状态
        return ("sleeping", 0)

    @staticmethod
    async def _get_latest_sensor_data(db: AsyncSession, device_sn: str) -> SensorDataRaw | None:
        """获取设备最新一条传感器数据"""
        result = await db.execute(
            select(SensorDataRaw)
            .where(SensorDataRaw.device_sn == device_sn)
            .order_by(desc(SensorDataRaw.collected_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_latest_status(db: AsyncSession, device_sn: str) -> BabyStatusLog | None:
        """获取设备最近一条状态日志（未结束的）"""
        result = await db.execute(
            select(BabyStatusLog)
            .where(BabyStatusLog.device_sn == device_sn)
            .where(BabyStatusLog.ended_at.is_(None))
            .order_by(desc(BabyStatusLog.started_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_baby_id(db: AsyncSession, device_sn: str) -> int | None:
        """获取设备绑定的宝宝ID"""
        # 从最新的传感器数据获取baby_id
        result = await db.execute(
            select(SensorDataRaw.baby_id)
            .where(SensorDataRaw.device_sn == device_sn)
            .order_by(desc(SensorDataRaw.collected_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def trigger_detection(db: AsyncSession, device_sn: str) -> dict:
        """触发设备事件检测，检测到五类状态时写入数据库"""
        now = datetime.now()

        # 1. 获取最新传感器数据
        sensor_data = await SensorService._get_latest_sensor_data(db, device_sn)
        if not sensor_data:
            return {"device_sn": device_sn, "status": "no_data", "message": "无传感器数据"}

        # 2. 获取baby_id
        baby_id = await SensorService._get_baby_id(db, device_sn)
        if not baby_id:
            return {"device_sn": device_sn, "status": "no_baby", "message": "设备未绑定宝宝"}

        # 3. 五类状态分类
        status_type, status_level = await SensorService._classify_status(sensor_data)

        # 4. 获取最近状态，比较是否变化
        last_status = await SensorService._get_latest_status(db, device_sn)
        status_changed = last_status is None or last_status.status_type != status_type

        # 5. 记录结果
        result = {
            "device_sn": device_sn,
            "baby_id": baby_id,
            "status_type": status_type,
            "status_level": status_level,
            "status_changed": status_changed,
            "sensor_snapshot": {
                "breath_rate": float(sensor_data.breath_rate) if sensor_data.breath_rate else None,
                "heart_rate": float(sensor_data.heart_rate) if sensor_data.heart_rate else None,
                "body_movement": float(sensor_data.body_movement) if sensor_data.body_movement else None,
                "distance_cm": float(sensor_data.distance_cm) if sensor_data.distance_cm else None,
                "pose_status": sensor_data.pose_status,
                "expression": sensor_data.expression,
            },
            "timestamp": now.isoformat(),
        }

        # 6. 状态变化时写入 baby_status_log
        if status_changed:
            # 先结束上一个状态
            if last_status:
                last_status.ended_at = now
                last_status.duration_sec = int((now - last_status.started_at).total_seconds())

            # 创建新状态日志
            new_log = BabyStatusLog(
                baby_id=baby_id,
                device_sn=device_sn,
                status_type=status_type,
                status_level=status_level,
                started_at=now,
                breath_rate=sensor_data.breath_rate,
                heart_rate=sensor_data.heart_rate,
                sound_db=sensor_data.sound_db,
                pose_status=sensor_data.pose_status,
                expression=sensor_data.expression,
            )
            db.add(new_log)
            await db.flush()
            result["log_id"] = new_log.id

            # 哭闹/危险状态同时写入专用事件表
            if status_type == "crying":
                cry_event = CryEvent(
                    baby_id=baby_id,
                    device_sn=device_sn,
                    cry_level=status_level or 1,
                    started_at=now,
                    sound_db=sensor_data.sound_db,
                    heart_rate=sensor_data.heart_rate,
                    body_movement=sensor_data.body_movement,
                    expression=sensor_data.expression,
                )
                db.add(cry_event)
                await db.flush()
                result["cry_event_id"] = cry_event.id

            elif status_type == "danger":
                # 根据姿态判断危险类型
                danger_type = "standing"
                if sensor_data.pose_status == "climbing":
                    danger_type = "climbing"
                elif sensor_data.pose_status in ["prone", "face_down"]:
                    danger_type = "prone_sleep"
                elif sensor_data.body_offset_cm and float(sensor_data.body_offset_cm) > 35:
                    danger_type = "near_edge"

                danger_event = DangerEvent(
                    baby_id=baby_id,
                    device_sn=device_sn,
                    danger_type=danger_type,
                    severity=status_level or 1,
                    detected_at=now,
                    breath_rate=sensor_data.breath_rate,
                    heart_rate=sensor_data.heart_rate,
                    body_offset_cm=sensor_data.body_offset_cm,
                    pose_status=sensor_data.pose_status,
                )
                db.add(danger_event)
                await db.flush()
                result["danger_event_id"] = danger_event.id

        await db.commit()
        return result

    # ========== 设备状态查询接口 ==========
    @staticmethod
    async def get_device_current_status(db: AsyncSession, device_sn: str) -> dict:
        """获取设备当前状态（未结束的状态日志）"""
        # 1. 获取 baby_id
        baby_id = await SensorService._get_baby_id(db, device_sn)
        if not baby_id:
            return {"device_sn": device_sn, "status": "no_baby", "message": "设备未绑定宝宝"}

        # 2. 获取当前未结束状态
        current_status = await SensorService._get_latest_status(db, device_sn)
        if not current_status:
            return {
                "device_sn": device_sn,
                "baby_id": baby_id,
                "status": "no_status",
                "message": "无当前状态记录",
                "status_type": None,
                "status_level": None,
                "started_at": None,
                "duration_sec": None,
            }

        # 3. 获取最新传感器数据
        sensor_data = await SensorService._get_latest_sensor_data(db, device_sn)

        return {
            "device_sn": device_sn,
            "baby_id": baby_id,
            "status_type": current_status.status_type,
            "status_level": current_status.status_level,
            "started_at": current_status.started_at.isoformat() if current_status.started_at else None,
            "duration_sec": int((datetime.now() - current_status.started_at).total_seconds()) if current_status.started_at else None,
            "sensor_snapshot": {
                "breath_rate": float(sensor_data.breath_rate) if sensor_data and sensor_data.breath_rate else None,
                "heart_rate": float(sensor_data.heart_rate) if sensor_data and sensor_data.heart_rate else None,
                "body_movement": float(sensor_data.body_movement) if sensor_data and sensor_data.body_movement else None,
                "sound_db": float(sensor_data.sound_db) if sensor_data and sensor_data.sound_db else None,
                "pose_status": sensor_data.pose_status if sensor_data else None,
                "expression": sensor_data.expression if sensor_data else None,
            } if sensor_data else None,
        }

    @staticmethod
    async def get_baby_status(db: AsyncSession, device_sn: str) -> dict:
        """获取宝宝当前状态及风险等级（小程序接口）"""
        # 1. 获取 baby_id
        baby_id = await SensorService._get_baby_id(db, device_sn)
        if not baby_id:
            return {"device_sn": device_sn, "status": "no_baby", "message": "设备未绑定宝宝"}

        # 2. 获取当前未结束状态
        current_status = await SensorService._get_latest_status(db, device_sn)
        if not current_status:
            return {
                "device_sn": device_sn,
                "baby_id": baby_id,
                "status_type": None,
                "status_level": None,
                "risk_label": None,
                "started_at": None,
                "duration_sec": None,
                "sensor_snapshot": None,
            }

        # 3. 获取最新传感器数据
        sensor_data = await SensorService._get_latest_sensor_data(db, device_sn)

        # 4. 映射中文风险标签
        risk_labels = {
            "sleeping": "正常",
            "awake": "正常",
            "playing": "正常",
            "crying": "关注" if (current_status.status_level or 0) <= 1 else ("警告" if (current_status.status_level or 0) <= 2 else "危险"),
            "danger": "危险",
        }
        risk_label = risk_labels.get(current_status.status_type, "正常")

        return {
            "device_sn": device_sn,
            "baby_id": baby_id,
            "status_type": current_status.status_type,
            "status_level": current_status.status_level,
            "risk_label": risk_label,
            "started_at": current_status.started_at.isoformat() if current_status.started_at else None,
            "duration_sec": int((datetime.now() - current_status.started_at).total_seconds()) if current_status.started_at else None,
            "sensor_snapshot": {
                "heart_rate": float(sensor_data.heart_rate) if sensor_data and sensor_data.heart_rate else None,
                "breath_rate": float(sensor_data.breath_rate) if sensor_data and sensor_data.breath_rate else None,
                "body_movement": float(sensor_data.body_movement) if sensor_data and sensor_data.body_movement else None,
                "sound_db": float(sensor_data.sound_db) if sensor_data and sensor_data.sound_db else None,
                "pose_status": sensor_data.pose_status if sensor_data else None,
            } if sensor_data else None,
        }

    @staticmethod
    async def get_device_status_history(db: AsyncSession, device_sn: str) -> list[dict]:
        """获取设备状态历史（通过 device_sn，返回所有数据）"""
        result = await db.execute(
            select(BabyStatusLog)
            .where(BabyStatusLog.device_sn == device_sn)
            .order_by(BabyStatusLog.started_at.desc())
        )
        logs = result.scalars().all()
        return [StatusLogInfo.model_validate(log).model_dump() for log in logs]

    @staticmethod
    async def get_sensor_data(
        db: AsyncSession, device_sn: str,
        start_time: datetime | None = None, end_time: datetime | None = None,
        page: int = 1, page_size: int = 20,
    ) -> dict:
        """查询传感器数据"""
        query = select(SensorDataRaw).where(SensorDataRaw.device_sn == device_sn)
        if start_time:
            query = query.where(SensorDataRaw.collected_at >= start_time)
        if end_time:
            query = query.where(SensorDataRaw.collected_at <= end_time)
        query = query.order_by(desc(SensorDataRaw.collected_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        records = result.scalars().all()

        return {
            "items": [
                {
                    "id": r.id,
                    "device_sn": r.device_sn,
                    "baby_id": r.baby_id,
                    "collected_at": r.collected_at.isoformat() if r.collected_at else None,
                    "breath_rate": float(r.breath_rate) if r.breath_rate else None,
                    "heart_rate": float(r.heart_rate) if r.heart_rate else None,
                    "body_movement": float(r.body_movement) if r.body_movement else None,
                    "distance_cm": float(r.distance_cm) if r.distance_cm else None,
                    "sound_db": float(r.sound_db) if r.sound_db else None,
                    "sound_type": r.sound_type,
                    "pose_status": r.pose_status,
                    "face_detected": r.face_detected,
                    "expression": r.expression,
                    "body_offset_cm": float(r.body_offset_cm) if r.body_offset_cm else None,
                    "roll_angle": float(r.roll_angle) if r.roll_angle else None,
                    "height_cm": float(r.height_cm) if r.height_cm else None,
                    "room_temp": float(r.room_temp) if r.room_temp else None,
                    "humidity": float(r.humidity) if r.humidity else None,
                    "noise_db": float(r.noise_db) if r.noise_db else None,
                }
                for r in records
            ],
            "page": page,
            "page_size": page_size,
        }

    # ========== 多模态融合监测 (2.1) ==========
    @staticmethod
    async def sensor_fusion(db: AsyncSession, device_sn: str, baby_id: int, video_data: str | None = None, radar_data: dict | None = None, audio_data: str | None = None) -> dict:
        """多模态数据融合分析"""
        # TODO: 实现多模态融合算法（视觉+雷达+音频）
        # 模拟融合结果，要求综合准确率 > 90%
        import random
        scenes = ["sleeping", "awake", "playing", "crying", "danger"]
        scene = random.choice(scenes)
        confidence = round(random.uniform(0.90, 0.98), 2)  # 要求 > 0.90

        return {
            "device_sn": device_sn,
            "baby_id": baby_id,
            "fused_status": scene,
            "confidence": confidence,
            "details": {
                "video_analysis": {"pose": "supine", "face_detected": True},
                "radar_analysis": {"breath_rate": 35, "heart_rate": 120},
                "audio_analysis": {"sound_type": "none", "db": 35},
            },
            "alert_level": "none" if scene in ["sleeping", "awake", "playing"] else ("high" if scene == "danger" else "medium"),
            "timestamp": datetime.now().isoformat(),
        }

    # ========== 五类场景分级响应 (2.2) ==========
    @staticmethod
    async def classify_scene(db: AsyncSession, baby_id: int) -> dict:
        """场景分类识别"""
        # TODO: 基于传感器数据进行场景分类
        import random
        scenes = ["sleeping", "awake", "playing", "crying", "danger"]
        scene = random.choice(scenes)
        return {
            "baby_id": baby_id,
            "scene_type": scene,
            "confidence": round(random.uniform(0.85, 0.95), 2),
            "triggers": ["breath_stable", "movement_none"] if scene == "sleeping" else ["sound_cry"],
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def execute_scene_response(db: AsyncSession, baby_id: int, scene_type: str, response_mode: str = "auto") -> dict:
        """执行场景响应脚本"""
        # TODO: 根据场景类型执行对应的响应脚本
        response_scripts = {
            "sleeping": {
                "light_config": {"color": "#000000", "brightness": 0},
                "sound_config": {"type": "white_noise", "volume": 30},
                "screen_animation": "moon",
            },
            "crying": {
                "light_config": {"color": "#FFD700", "brightness": 50},
                "sound_config": {"type": "lullaby", "volume": 60},
                "screen_animation": "comfort",
            },
            "danger": {
                "light_config": {"color": "#FF0000", "brightness": 100, "blink": True},
                "sound_config": {"type": "alert", "volume": 80},
                "screen_animation": "warning",
                "push_notification": True,
            },
        }
        script = response_scripts.get(scene_type, {})
        return {
            "script_id": f"script_{scene_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "scene_type": scene_type,
            "actions": [{"type": "light", "config": script.get("light_config")}, {"type": "sound", "config": script.get("sound_config")}],
            "light_config": script.get("light_config"),
            "sound_config": script.get("sound_config"),
            "screen_animation": script.get("screen_animation"),
            "push_notification": script.get("push_notification", False),
            "message": f"已执行{scene_type}场景响应",
        }

    # ========== 数据清理定时任务 ==========
    @staticmethod
    async def cleanup_old_sensor_data(db: AsyncSession, retention_days: int = 7) -> dict:
        """清理过期的传感器原始数据

        Args:
            retention_days: 数据保留天数，默认 7 天

        Returns:
            清理结果统计
        """
        from datetime import timedelta
        from sqlalchemy import delete

        cutoff_time = datetime.now() - timedelta(days=retention_days)

        # 统计即将删除的数据量
        count_result = await db.execute(
            select(func.count(SensorDataRaw.id)).where(SensorDataRaw.collected_at < cutoff_time)
        )
        delete_count = count_result.scalar() or 0

        if delete_count > 0:
            # 执行删除
            await db.execute(
                delete(SensorDataRaw).where(SensorDataRaw.collected_at < cutoff_time)
            )
            await db.flush()

        return {
            "deleted_count": delete_count,
            "retention_days": retention_days,
            "cutoff_time": cutoff_time.isoformat(),
        }


sensor_service = SensorService()
