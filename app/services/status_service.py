"""
状态日志业务逻辑层
"""
from datetime import datetime, date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.status_log import BabyStatusLog
from app.models.cry_event import CryEvent
from app.models.danger_event import DangerEvent
from app.models.sleep_report import SleepReport
from app.schemas.status import (
    StatusLogInfo,
    CryEventInfo,
    DangerEventInfo,
    SleepReportInfo,
)
from app.core.exceptions import NotFoundException


def _to_dict(obj) -> dict:
    """将 ORM 对象转换为 dict"""
    if obj is None:
        return None
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


class StatusService:
    """状态服务"""

    # ========== 状态日志 ==========
    @staticmethod
    async def create_status_log(db: AsyncSession, data: dict) -> dict:
        """创建状态日志"""
        log = BabyStatusLog(**data)
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return StatusLogInfo.model_validate(log).model_dump()

    @staticmethod
    async def end_status_log(db: AsyncSession, log_id: int, ended_at: datetime) -> dict:
        """结束状态日志"""
        result = await db.execute(select(BabyStatusLog).where(BabyStatusLog.id == log_id))
        log = result.scalar_one_or_none()
        if not log:
            raise NotFoundException("状态日志不存在")
        log.ended_at = ended_at
        log.duration_sec = int((ended_at - log.started_at).total_seconds())
        await db.commit()
        await db.refresh(log)
        return {
            "id": log.id,
            "duration_sec": log.duration_sec,
        }

    @staticmethod
    async def get_status_history(db: AsyncSession, baby_id: int, start_date: date, end_date: date) -> list[dict]:
        """获取状态历史"""
        result = await db.execute(
            select(BabyStatusLog)
            .where(and_(
                BabyStatusLog.baby_id == baby_id,
                BabyStatusLog.started_at >= start_date,
                BabyStatusLog.started_at < end_date + timedelta(days=1),
            ))
            .order_by(BabyStatusLog.started_at.desc())
        )
        logs = result.scalars().all()
        return [StatusLogInfo.model_validate(log).model_dump() for log in logs]

    # ========== 哭闹事件 ==========
    @staticmethod
    async def create_cry_event(db: AsyncSession, data: dict) -> dict:
        """创建哭闹事件"""
        event = CryEvent(**data)
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return {"id": event.id}

    @staticmethod
    async def handle_cry_event(db: AsyncSession, event_id: int, handle_method: str) -> dict:
        """处理哭闹事件"""
        result = await db.execute(select(CryEvent).where(CryEvent.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise NotFoundException("哭闹事件不存在")
        event.parent_handled = 1
        event.handled_at = datetime.now()
        event.handle_method = handle_method
        await db.commit()
        await db.refresh(event)
        return {"id": event.id}

    @staticmethod
    async def get_cry_events(db: AsyncSession, baby_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取哭闹事件列表"""
        result = await db.execute(
            select(CryEvent)
            .where(CryEvent.baby_id == baby_id)
            .order_by(CryEvent.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        events = result.scalars().all()
        return {
            "items": [CryEventInfo.model_validate(e).model_dump() for e in events],
            "page": page,
            "page_size": page_size,
        }

    # ========== 危险事件 ==========
    @staticmethod
    async def create_danger_event(db: AsyncSession, data: dict) -> dict:
        """创建危险事件"""
        event = DangerEvent(**data)
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return {"id": event.id}

    @staticmethod
    async def handle_danger_event(db: AsyncSession, event_id: int, handle_result: str) -> dict:
        """处理危险事件"""
        result = await db.execute(select(DangerEvent).where(DangerEvent.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise NotFoundException("危险事件不存在")
        event.parent_handled = 1
        event.handled_at = datetime.now()
        event.handle_result = handle_result
        await db.commit()
        await db.refresh(event)
        return {"id": event.id}

    @staticmethod
    async def get_danger_events(db: AsyncSession, baby_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取危险事件列表"""
        result = await db.execute(
            select(DangerEvent)
            .where(DangerEvent.baby_id == baby_id)
            .order_by(DangerEvent.detected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        events = result.scalars().all()
        return {
            "items": [DangerEventInfo.model_validate(e).model_dump() for e in events],
            "page": page,
            "page_size": page_size,
        }

    # ========== 睡眠报告 ==========
    @staticmethod
    async def get_sleep_report(db: AsyncSession, baby_id: int, report_date: date) -> dict | None:
        """获取睡眠报告"""
        result = await db.execute(
            select(SleepReport)
            .where(and_(SleepReport.baby_id == baby_id, SleepReport.report_date == report_date))
        )
        report = result.scalar_one_or_none()
        if report:
            return SleepReportInfo.model_validate(report).model_dump()
        return None

    @staticmethod
    async def generate_sleep_report(db: AsyncSession, baby_id: int, report_date: date) -> dict:
        """生成睡眠报告"""
        start_dt = datetime.combine(report_date, datetime.min.time())
        end_dt = datetime.combine(report_date, datetime.max.time())

        result = await db.execute(
            select(BabyStatusLog)
            .where(and_(
                BabyStatusLog.baby_id == baby_id,
                BabyStatusLog.status_type == "sleeping",
                BabyStatusLog.started_at >= start_dt,
                BabyStatusLog.started_at <= end_dt,
            ))
        )
        sleep_logs = result.scalars().all()

        total_sleep_min = sum(log.duration_sec or 0 for log in sleep_logs) // 60

        report = SleepReport(
            baby_id=baby_id,
            report_date=report_date,
            total_sleep_min=total_sleep_min,
            nap_count=len(sleep_logs),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return SleepReportInfo.model_validate(report).model_dump()


status_service = StatusService()
