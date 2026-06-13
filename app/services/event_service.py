"""
监测事件业务逻辑层
"""
from datetime import datetime
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.monitoring import MonitoringEvent
from app.models.passive_event import PassiveEventType
from app.models.family_member import FamilyMember
from app.services.family_service import FamilyService
from app.models.status_log import BabyStatusLog
from app.models.cry_event import CryEvent
from app.models.danger_event import DangerEvent


class EventService:
    """监测事件服务"""

    @staticmethod
    async def create_event(db: AsyncSession, **kwargs) -> dict:
        """创建监测事件"""
        event = MonitoringEvent(**kwargs)
        db.add(event)
        await db.flush()
        return {"id": event.id, "message": "事件已记录"}

    @staticmethod
    async def get_events(
        db: AsyncSession, user_id: int,
        device_sn: str | None = None, baby_id: int | None = None,
        event_type_id: int | None = None, event_level: int | None = None,
        page: int = 1, page_size: int = 20,
    ) -> dict:
        """查询监测事件列表（联合 baby_status_log / cry_event / danger_event）"""
        try:
            family = await FamilyService._get_user_family_obj(db, user_id)
            from app.models.baby import Baby
            result = await db.execute(select(Baby.id).where(Baby.family_id == family.id))
            baby_ids = [row[0] for row in result.all()]
            print(f"[DEBUG] get_events: user_id={user_id}, family_id={family.id}, baby_ids={baby_ids}")
        except Exception as e:
            # 打印错误以便调试
            import traceback
            traceback.print_exc()
            raise Exception(f"获取家庭信息失败: {str(e)}")

        # 如果没有宝宝，返回空
        if not baby_ids:
            return {
                "items": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
            }

        # event_type_id 1-5: sleeping/awake/playing/crying/danger
        status_type_map = {
            1: "sleeping",
            2: "awake",
            3: "playing",
            4: "crying",
            5: "danger",
        }
        target_status = status_type_map.get(event_type_id) if event_type_id else None

        items = []

        # 1. 查询 baby_status_log
        status_query = select(BabyStatusLog).where(BabyStatusLog.baby_id.in_(baby_ids))
        if device_sn:
            status_query = status_query.where(BabyStatusLog.device_sn == device_sn)
        if baby_id:
            status_query = status_query.where(BabyStatusLog.baby_id == baby_id)
        if target_status:
            status_query = status_query.where(BabyStatusLog.status_type == target_status)
        if event_level is not None:
            status_query = status_query.where(BabyStatusLog.status_level == event_level)

        status_result = await db.execute(status_query.order_by(desc(BabyStatusLog.started_at)))
        status_records = status_result.scalars().all()
        print(f"[DEBUG] baby_status_log query result count: {len(status_records)}")
        for s in status_records:
            items.append({
                "id": s.id,
                "baby_id": s.baby_id,
                "device_sn": s.device_sn,
                "event_type": s.status_type,
                "event_level": s.status_level,
                "detected_at": s.started_at.isoformat() if s.started_at else None,
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "duration_sec": s.duration_sec,
                "breath_rate": float(s.breath_rate) if s.breath_rate else None,
                "heart_rate": float(s.heart_rate) if s.heart_rate else None,
                "sound_db": float(s.sound_db) if s.sound_db else None,
                "source_table": "baby_status_log",
                "source_ref": f"status_log_{s.id}",
            })

        # 2. 查询 cry_event（如果不是只查 sleeping/awake/playing 才查）
        if target_status in [None, "crying"]:
            cry_query = select(CryEvent).where(CryEvent.baby_id.in_(baby_ids))
            if device_sn:
                cry_query = cry_query.where(CryEvent.device_sn == device_sn)
            if baby_id:
                cry_query = cry_query.where(CryEvent.baby_id == baby_id)

            cry_result = await db.execute(cry_query.order_by(desc(CryEvent.started_at)))
            cry_records = cry_result.scalars().all()
            print(f"[DEBUG] cry_event query result count: {len(cry_records)}")
            for c in cry_records:
                items.append({
                    "id": c.id,
                    "baby_id": c.baby_id,
                    "device_sn": c.device_sn,
                    "event_type": "crying",
                    "event_level": c.cry_level,
                    "detected_at": c.started_at.isoformat() if c.started_at else None,
                    "ended_at": c.ended_at.isoformat() if c.ended_at else None,
                    "duration_sec": c.duration_sec,
                    "parent_handled": c.parent_handled,
                    "breath_rate": None,
                    "heart_rate": float(c.heart_rate) if c.heart_rate else None,
                    "sound_db": float(c.sound_db) if c.sound_db else None,
                    "source_table": "cry_event",
                    "source_ref": f"cry_{c.id}",
                })

        # 3. 查询 danger_event（如果不是只查 sleeping/awake/playing 才查）
        if target_status in [None, "danger"]:
            danger_query = select(DangerEvent).where(DangerEvent.baby_id.in_(baby_ids))
            if device_sn:
                danger_query = danger_query.where(DangerEvent.device_sn == device_sn)
            if baby_id:
                danger_query = danger_query.where(DangerEvent.baby_id == baby_id)

            danger_result = await db.execute(danger_query.order_by(desc(DangerEvent.detected_at)))
            danger_records = danger_result.scalars().all()
            print(f"[DEBUG] danger_event query result count: {len(danger_records)}")
            for d in danger_records:
                items.append({
                    "id": d.id,
                    "baby_id": d.baby_id,
                    "device_sn": d.device_sn,
                    "event_type": "danger",
                    "event_level": d.severity,
                    "detected_at": d.detected_at.isoformat() if d.detected_at else None,
                    "ended_at": d.ended_at.isoformat() if d.ended_at else None,
                    "duration_sec": d.duration_sec,
                    "parent_handled": d.parent_handled,
                    "breath_rate": float(d.breath_rate) if d.breath_rate else None,
                    "heart_rate": float(d.heart_rate) if d.heart_rate else None,
                    "sound_db": None,
                    "source_table": "danger_event",
                    "source_ref": f"danger_{d.id}",
                })

        # 按 detected_at 降序排序后分页
        items.sort(key=lambda x: x["detected_at"] or "", reverse=True)
        total = len(items)
        paged = items[(page - 1) * page_size:page * page_size]
        print(f"[DEBUG] Final result: total={total}, items_count={len(paged)}")

        return {
            "items": paged,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    @staticmethod
    async def get_event_detail(db: AsyncSession, user_id: int, event_id: int) -> dict:
        """获取事件详情"""
        result = await db.execute(select(MonitoringEvent).where(MonitoringEvent.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise NotFoundException("事件不存在")
        return {
            "id": event.id,
            "baby_id": event.baby_id,
            "device_sn": event.device_sn,
            "event_type_id": event.event_type_id,
            "event_level": event.event_level,
            "trigger_source": event.trigger_source,
            "breath_rate": float(event.breath_rate) if event.breath_rate else None,
            "heart_rate": float(event.heart_rate) if event.heart_rate else None,
            "sound_db": float(event.sound_db) if event.sound_db else None,
            "body_displace_cm": float(event.body_displace_cm) if event.body_displace_cm else None,
            "pose_angle": float(event.pose_angle) if event.pose_angle else None,
            "detected_at": event.detected_at.isoformat() if event.detected_at else None,
            "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
            "duration_sec": event.duration_sec,
            "screen_acted": event.screen_acted,
            "sound_acted": event.sound_acted,
            "app_pushed": event.app_pushed,
            "parent_handled": event.parent_handled,
            "handled_at": event.handled_at.isoformat() if event.handled_at else None,
            "snapshot_url": event.snapshot_url,
            "video_clip_url": event.video_clip_url,
            "gif_url": event.gif_url,
            "remark": event.remark,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    @staticmethod
    async def confirm_event(db: AsyncSession, event_id: int, parent_handled: int = 1) -> dict:
        """确认事件"""
        result = await db.execute(select(MonitoringEvent).where(MonitoringEvent.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise NotFoundException("事件不存在")

        event.parent_handled = parent_handled
        event.handled_at = datetime.now()
        return {"id": event.id, "message": "确认成功"}

    @staticmethod
    async def get_passive_event_types(db: AsyncSession, category: str | None = None) -> list[dict]:
        """获取被动事件类型列表"""
        query = select(PassiveEventType).where(PassiveEventType.is_active == 1)
        if category:
            query = query.where(PassiveEventType.category == category)
        query = query.order_by(PassiveEventType.sort_order)

        result = await db.execute(query)
        types = result.scalars().all()
        return [
            {
                "id": t.id,
                "parent_id": t.parent_id,
                "event_code": t.event_code,
                "event_name": t.event_name,
                "category": t.category,
                "priority": t.priority,
                "trigger_desc": t.trigger_desc,
                "screen_response": t.screen_response,
                "sound_response": t.sound_response,
                "app_response": t.app_response,
                "sort_order": t.sort_order,
            }
            for t in types
        ]

    @staticmethod
    async def get_event_type_detail(db: AsyncSession, event_type_id: int) -> dict:
        """获取事件类型详情"""
        result = await db.execute(select(PassiveEventType).where(PassiveEventType.id == event_type_id))
        t = result.scalar_one_or_none()
        if not t:
            raise NotFoundException("事件类型不存在")
        return {
            "id": t.id,
            "parent_id": t.parent_id,
            "event_code": t.event_code,
            "event_name": t.event_name,
            "category": t.category,
            "priority": t.priority,
            "trigger_desc": t.trigger_desc,
            "screen_response": t.screen_response,
            "sound_response": t.sound_response,
            "app_response": t.app_response,
            "sort_order": t.sort_order,
            "is_active": t.is_active,
        }

    @staticmethod
    async def get_response_history(db: AsyncSession, user_id: int, baby_id: int, category: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        """获取被动响应历史（基于监测事件）"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        from app.models.baby import Baby
        result = await db.execute(select(Baby.id).where(Baby.family_id == family.id))
        baby_ids = [row[0] for row in result.all()]

        query = select(MonitoringEvent).where(MonitoringEvent.baby_id.in_(baby_ids))
        if baby_id:
            query = query.where(MonitoringEvent.baby_id == baby_id)
        if category:
            # 根据category查找对应的事件类型ID
            type_result = await db.execute(select(PassiveEventType.id).where(PassiveEventType.category == category))
            type_ids = [row[0] for row in type_result.all()]
            if type_ids:
                query = query.where(MonitoringEvent.event_type_id.in_(type_ids))

        query = query.order_by(desc(MonitoringEvent.detected_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        events = result.scalars().all()

        return {
            "items": [
                {
                    "id": e.id,
                    "baby_id": e.baby_id,
                    "event_type_id": e.event_type_id,
                    "event_level": e.event_level,
                    "detected_at": e.detected_at.isoformat() if e.detected_at else None,
                    "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
                    "parent_handled": e.parent_handled,
                    "screen_acted": e.screen_acted,
                    "sound_acted": e.sound_acted,
                }
                for e in events
            ],
            "page": page,
            "page_size": page_size,
        }


event_service = EventService()
