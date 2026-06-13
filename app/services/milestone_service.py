"""
成长里程碑业务逻辑层
"""
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.milestone import GrowthMilestone
from app.services.family_service import FamilyService


class MilestoneService:
    """成长里程碑服务"""

    @staticmethod
    async def create_milestone(db: AsyncSession, user_id: int, **kwargs) -> dict:
        """创建里程碑"""
        milestone = GrowthMilestone(**kwargs)
        db.add(milestone)
        await db.flush()
        return {"id": milestone.id, "message": "创建成功"}

    @staticmethod
    async def get_milestone_list(db: AsyncSession, user_id: int, baby_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取里程碑列表"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        from app.models.baby import Baby
        result = await db.execute(select(Baby.id).where(Baby.family_id == family.id))
        baby_ids = [row[0] for row in result.all()]

        query = select(GrowthMilestone).where(GrowthMilestone.baby_id.in_(baby_ids))
        if baby_id:
            query = query.where(GrowthMilestone.baby_id == baby_id)
        query = query.order_by(desc(GrowthMilestone.detected_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        milestones = result.scalars().all()
        return {
            "items": [
                {
                    "id": m.id,
                    "baby_id": m.baby_id,
                    "event_type_id": m.event_type_id,
                    "milestone_code": m.milestone_code,
                    "milestone_name": m.milestone_name,
                    "milestone_desc": m.milestone_desc,
                    "age_months": m.age_months,
                    "snapshot_url": m.snapshot_url,
                    "gif_url": m.gif_url,
                    "video_clip_url": m.video_clip_url,
                    "detected_at": m.detected_at.isoformat() if m.detected_at else None,
                    "is_highlight": m.is_highlight,
                }
                for m in milestones
            ],
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def get_milestone_detail(db: AsyncSession, user_id: int, milestone_id: int) -> dict:
        """获取里程碑详情"""
        result = await db.execute(select(GrowthMilestone).where(GrowthMilestone.id == milestone_id))
        m = result.scalar_one_or_none()
        if not m:
            raise NotFoundException("里程碑不存在")
        return {
            "id": m.id,
            "baby_id": m.baby_id,
            "event_type_id": m.event_type_id,
            "milestone_code": m.milestone_code,
            "milestone_name": m.milestone_name,
            "milestone_desc": m.milestone_desc,
            "age_months": m.age_months,
            "snapshot_url": m.snapshot_url,
            "gif_url": m.gif_url,
            "video_clip_url": m.video_clip_url,
            "gif_size_bytes": m.gif_size_bytes,
            "detected_at": m.detected_at.isoformat() if m.detected_at else None,
            "is_highlight": m.is_highlight,
            "week_report_included": m.week_report_included,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }

    @staticmethod
    async def delete_milestone(db: AsyncSession, user_id: int, milestone_id: int) -> None:
        """删除里程碑"""
        result = await db.execute(select(GrowthMilestone).where(GrowthMilestone.id == milestone_id))
        m = result.scalar_one_or_none()
        if not m:
            raise NotFoundException("里程碑不存在")
        await db.delete(m)

    # ========== 关键事件自动固化 (3.2) ==========
    @staticmethod
    async def capture_event_video(db: AsyncSession, user_id: int, baby_id: int, event_type: str, trigger_time: datetime, pre_seconds: int = 3, post_seconds: int = 5) -> dict:
        """截取事件视频"""
        # TODO: 调用视频处理服务截取前3s后5s
        import uuid
        capture_id = uuid.uuid4().hex[:16]
        duration = pre_seconds + post_seconds

        return {
            "capture_id": capture_id,
            "baby_id": baby_id,
            "event_type": event_type,
            "video_url": f"/uploads/captures/{capture_id}.mp4",
            "gif_url": None,  # 异步生成
            "gif_size_bytes": None,
            "duration_sec": duration,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
        }

    @staticmethod
    async def generate_gif(db: AsyncSession, user_id: int, capture_id: str, quality: str = "medium", max_size_mb: float = 2.0) -> dict:
        """生成GIF动图"""
        # TODO: 调用GIF生成服务，要求<2MB
        import random
        gif_size = round(random.uniform(1.0, 1.8), 2)  # MB, 要求<2MB

        return {
            "capture_id": capture_id,
            "gif_url": f"/uploads/gifs/{capture_id}.gif",
            "gif_size_bytes": int(gif_size * 1024 * 1024),
            "gif_size_mb": gif_size,
            "quality": quality,
            "status": "completed",
            "generated_at": datetime.now().isoformat(),
        }

    # ========== AI成长周报 (3.3) ==========
    @staticmethod
    async def generate_weekly_report(db: AsyncSession, user_id: int, baby_id: int, week_start: datetime | None = None) -> dict:
        """生成AI成长周报"""
        # TODO: 汇总LTM数据，调用LLM生成周报
        import uuid
        from datetime import timedelta

        if week_start is None:
            # 默认上周日
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday() + 1)
        week_end = week_start + timedelta(days=6)

        report_id = uuid.uuid4().hex[:16]

        return {
            "report_id": report_id,
            "baby_id": baby_id,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "title": f"宝宝成长周报 ({week_start.strftime('%m/%d')}-{week_end.strftime('%m/%d')})",
            "summary": "本周宝宝睡眠质量良好，共记录了3个新里程碑。",
            "highlights": [
                {"type": "milestone", "title": "第一次翻身", "date": "2024-01-15"},
                {"type": "sleep", "title": "连续睡眠6小时", "date": "2024-01-17"},
            ],
            "milestones": [
                {"name": "翻身", "date": "2024-01-15", "gif_url": "/uploads/gifs/xxx.gif"},
            ],
            "sleep_analysis": {
                "total_sleep_hours": 56,
                "avg_night_sleep": 8.5,
                "naps_count": 14,
            },
            "feeding_analysis": {
                "total_feedings": 35,
                "avg_daily_feedings": 5,
            },
            "recommendations": [
                "建议增加白天活动时间",
                "晚间入睡时间可适当延后",
            ],
            "status": "completed",
            "generated_at": datetime.now().isoformat(),
        }


milestone_service = MilestoneService()
