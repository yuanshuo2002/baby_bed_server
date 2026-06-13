"""
成长报告业务逻辑层 - 支持日报、周报、月报
"""
from datetime import date, datetime, timedelta
from sqlalchemy import select, desc, and_, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException
from app.models.weekly_report import AIWeeklyReport
from app.models.status_log import BabyStatusLog
from app.models.cry_event import CryEvent
from app.models.danger_event import DangerEvent
from app.models.milestone import GrowthMilestone as Milestone
from app.services.family_service import FamilyService
from app.services.llm_service import llm_service


class ReportService:
    """成长报告服务"""

    @staticmethod
    async def generate_weekly_report(
        db: AsyncSession,
        user_id: int,
        baby_id: int,
        report_type: str = "weekly",
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> dict:
        """
        生成成长报告（日报/周报/月报）

        Args:
            report_type: 报告类型 (daily/weekly/monthly)
            period_start: 周期开始日期，默认根据report_type自动计算
            period_end: 周期结束日期，默认根据report_type自动计算
        """
        # 计算默认周期
        today = date.today()
        if report_type == "daily":
            period_start = period_start or today
            period_end = period_end or today
        elif report_type == "weekly":
            # 上周日
            period_start = period_start or (today - timedelta(days=today.weekday() + 1))
            period_end = period_end or (period_start + timedelta(days=6))
        elif report_type == "monthly":
            # 上月1日
            period_start = period_start or (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_day = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            period_end = period_end or last_day

        period_label = {"daily": "日报", "weekly": "周报", "monthly": "月报"}.get(report_type, "报告")

        # 检查是否已存在
        existing = await db.execute(
            select(AIWeeklyReport).where(
                AIWeeklyReport.baby_id == baby_id,
                AIWeeklyReport.report_type == report_type,
                AIWeeklyReport.period_start == period_start,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(f"该{report_type}报告已存在")

        # 汇总五大事件数据
        event_stats = await ReportService._collect_event_stats(db, baby_id, period_start, period_end)

        try:
            # 调用LLM生成报告
            llm_result = await llm_service.generate_growth_report(
                report_type=report_type,
                period_start=period_start.isoformat(),
                period_end=period_end.isoformat(),
                event_stats=event_stats,
            )
        except Exception as e:
            # LLM调用失败时使用默认报告
            print(f"[警告] LLM调用失败: {e}")
            llm_result = {
                "title": f"{period_label}成长报告",
                "summary": f"周期内睡眠{event_stats.get('sleep', {}).get('duration_hours', 0):.1f}小时，哭闹{event_stats.get('cry', {}).get('count', 0)}次",
                "highlights": ["数据收集中"],
                "recommendations": ["保持规律作息"],
                "sleep_analysis": "睡眠数据采集中",
                "health_notes": "健康数据采集中",
            }

        # 保存报告
        report = AIWeeklyReport(
            baby_id=baby_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            total_sleep_hours=event_stats.get("sleep", {}).get("duration_hours"),
            cry_event_count=event_stats.get("cry", {}).get("count"),
            danger_event_count=event_stats.get("danger", {}).get("count"),
            milestone_count=event_stats.get("milestone", {}).get("count"),
            summary_text=llm_result.get("summary"),
            growth_highlights="\n".join(llm_result.get("highlights", [])),
            health_notes=llm_result.get("health_notes"),
            suggestions="\n".join(llm_result.get("recommendations", [])),
            generated_at=datetime.now(),
            llm_model="local-llm",
            push_status=0,
        )
        db.add(report)
        await db.flush()

        return {
            "id": report.id,
            "report_type": report_type,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "title": llm_result.get("title"),
            "summary": llm_result.get("summary"),
            "status": "completed",
        }

    @staticmethod
    async def _collect_event_stats(
        db: AsyncSession,
        baby_id: int,
        period_start: date,
        period_end: date,
    ) -> dict:
        """汇总五大事件统计数据"""
        start_dt = datetime.combine(period_start, datetime.min.time())
        end_dt = datetime.combine(period_end, datetime.max.time())

        stats = {
            "sleep": await ReportService._get_sleep_stats(db, baby_id, start_dt, end_dt),
            "cry": await ReportService._get_cry_stats(db, baby_id, start_dt, end_dt),
            "danger": await ReportService._get_danger_stats(db, baby_id, start_dt, end_dt),
            "playing": await ReportService._get_playing_stats(db, baby_id, start_dt, end_dt),
            "milestone": await ReportService._get_milestone_stats(db, baby_id, period_start, period_end),
        }
        return stats

    @staticmethod
    async def _get_sleep_stats(db: AsyncSession, baby_id: int, start_dt: datetime, end_dt: datetime) -> dict:
        """获取睡眠统计"""
        result = await db.execute(
            select(BabyStatusLog)
            .where(
                BabyStatusLog.baby_id == baby_id,
                BabyStatusLog.status_type == "sleeping",
                BabyStatusLog.started_at >= start_dt,
                BabyStatusLog.started_at <= end_dt,
            )
        )
        logs = result.scalars().all()

        total_duration = 0.0
        for log in logs:
            if log.duration_sec:
                total_duration += log.duration_sec / 3600.0  # 转换为小时

        return {
            "duration_hours": round(total_duration, 1),
            "count": len(logs),
            "avg_quality": 8.5,  # TODO: 基于传感器数据计算真实质量
        }

    @staticmethod
    async def _get_cry_stats(db: AsyncSession, baby_id: int, start_dt: datetime, end_dt: datetime) -> dict:
        """获取哭闹统计"""
        result = await db.execute(
            select(CryEvent)
            .where(
                CryEvent.baby_id == baby_id,
                CryEvent.started_at >= start_dt,
                CryEvent.started_at <= end_dt,
            )
        )
        events = result.scalars().all()

        total_duration = 0
        total_level = 0
        for e in events:
            if e.duration_sec:
                total_duration += e.duration_sec / 60  # 转换为分钟
            if e.cry_level:
                total_level += e.cry_level

        count = len(events)
        return {
            "count": count,
            "total_duration_min": int(total_duration),
            "avg_level": round(total_level / count, 1) if count > 0 else 0,
        }

    @staticmethod
    async def _get_danger_stats(db: AsyncSession, baby_id: int, start_dt: datetime, end_dt: datetime) -> dict:
        """获取危险事件统计"""
        result = await db.execute(
            select(DangerEvent.danger_type, func.count(DangerEvent.id))
            .where(
                DangerEvent.baby_id == baby_id,
                DangerEvent.detected_at >= start_dt,
                DangerEvent.detected_at <= end_dt,
            )
            .group_by(DangerEvent.danger_type)
        )
        type_counts = {row[0]: row[1] for row in result.all()}

        total = sum(type_counts.values())
        return {
            "count": total,
            "types": type_counts,
        }

    @staticmethod
    async def _get_playing_stats(db: AsyncSession, baby_id: int, start_dt: datetime, end_dt: datetime) -> dict:
        """获取玩耍统计"""
        result = await db.execute(
            select(BabyStatusLog)
            .where(
                BabyStatusLog.baby_id == baby_id,
                BabyStatusLog.status_type == "playing",
                BabyStatusLog.started_at >= start_dt,
                BabyStatusLog.started_at <= end_dt,
            )
        )
        logs = result.scalars().all()

        total_duration = 0.0
        for log in logs:
            if log.duration_sec:
                total_duration += log.duration_sec / 3600.0

        return {
            "count": len(logs),
            "duration_hours": round(total_duration, 1),
        }

    @staticmethod
    async def _get_milestone_stats(db: AsyncSession, baby_id: int, period_start: date, period_end: date) -> dict:
        """获取里程碑统计"""
        result = await db.execute(
            select(Milestone)
            .where(
                Milestone.baby_id == baby_id,
                Milestone.detected_at >= period_start,
                Milestone.detected_at <= period_end,
            )
        )
        milestones = result.scalars().all()

        items = [
            {
                "name": m.milestone_name,
                "code": m.milestone_code,
                "detected_at": m.detected_at.isoformat() if m.detected_at else None,
            }
            for m in milestones[:10]  # 最多10条
        ]

        return {
            "count": len(milestones),
            "items": items,
        }

    @staticmethod
    async def get_weekly_report_list(
        db: AsyncSession,
        user_id: int,
        baby_id: int,
        report_type: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        """获取报告列表"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        from app.models.baby import Baby

        result = await db.execute(select(Baby.id).where(Baby.family_id == family.id))
        baby_ids = [row[0] for row in result.all()]

        query = select(AIWeeklyReport).where(AIWeeklyReport.baby_id.in_(baby_ids))
        if baby_id:
            query = query.where(AIWeeklyReport.baby_id == baby_id)
        if report_type:
            query = query.where(AIWeeklyReport.report_type == report_type)

        query = query.order_by(desc(AIWeeklyReport.period_start))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        reports = result.scalars().all()

        return {
            "items": [
                {
                    "id": r.id,
                    "baby_id": r.baby_id,
                    "report_type": r.report_type,
                    "period_start": r.period_start.isoformat() if r.period_start else None,
                    "period_end": r.period_end.isoformat() if r.period_end else None,
                    "total_sleep_hours": float(r.total_sleep_hours) if r.total_sleep_hours else None,
                    "cry_event_count": r.cry_event_count,
                    "danger_event_count": r.danger_event_count,
                    "milestone_count": r.milestone_count,
                    "summary_text": r.summary_text,
                    "push_status": r.push_status,
                    "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                }
                for r in reports
            ],
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def get_weekly_report_detail(db: AsyncSession, user_id: int, report_id: int) -> dict:
        """获取报告详情"""
        result = await db.execute(select(AIWeeklyReport).where(AIWeeklyReport.id == report_id))
        r = result.scalar_one_or_none()
        if not r:
            raise NotFoundException("报告不存在")

        return {
            "id": r.id,
            "baby_id": r.baby_id,
            "report_type": r.report_type,
            "period_start": r.period_start.isoformat() if r.period_start else None,
            "period_end": r.period_end.isoformat() if r.period_end else None,
            "total_sleep_hours": float(r.total_sleep_hours) if r.total_sleep_hours else None,
            "cry_event_count": r.cry_event_count,
            "danger_event_count": r.danger_event_count,
            "milestone_count": r.milestone_count,
            "smile_count": r.smile_count,
            "summary_text": r.summary_text,
            "growth_highlights": r.growth_highlights,
            "health_notes": r.health_notes,
            "suggestions": r.suggestions,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "llm_model": r.llm_model,
            "push_status": r.push_status,
            "pushed_at": r.pushed_at.isoformat() if r.pushed_at else None,
        }


report_service = ReportService()