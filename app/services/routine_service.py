"""
作息管理业务逻辑层
"""
from datetime import date, time, datetime
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.routine import BabyRoutine
from app.models.routine_conflict import RoutineConflictLog
from app.services.family_service import FamilyService


class RoutineService:
    """作息管理服务"""

    @staticmethod
    async def create_routine(db: AsyncSession, user_id: int, **kwargs) -> dict:
        """创建作息计划"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        routine = BabyRoutine(**kwargs)
        db.add(routine)
        await db.flush()
        return {"id": routine.id, "message": "创建成功"}

    @staticmethod
    async def get_routine_list(db: AsyncSession, user_id: int, baby_id: int, activity_type: str | None = None) -> list[dict]:
        """获取作息列表"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        from app.models.baby import Baby
        result = await db.execute(select(Baby.id).where(Baby.family_id == family.id))
        baby_ids = [row[0] for row in result.all()]

        query = select(BabyRoutine).where(BabyRoutine.baby_id.in_(baby_ids), BabyRoutine.is_active == 1)
        if baby_id:
            query = query.where(BabyRoutine.baby_id == baby_id)
        if activity_type:
            query = query.where(BabyRoutine.activity_type == activity_type)
        query = query.order_by(BabyRoutine.time_slot)

        result = await db.execute(query)
        routines = result.scalars().all()
        return [
            {
                "id": r.id,
                "baby_id": r.baby_id,
                "template_name": r.template_name,
                "time_slot": r.time_slot.isoformat() if r.time_slot else None,
                "activity_type": r.activity_type,
                "activity_name": r.activity_name,
                "duration_min": r.duration_min,
                "reminder_enabled": r.reminder_enabled,
                "reminder_before_min": r.reminder_before_min,
                "effective_date": r.effective_date.isoformat() if r.effective_date else None,
                "expire_date": r.expire_date.isoformat() if r.expire_date else None,
                "is_auto_adjusted": r.is_auto_adjusted,
                "is_active": r.is_active,
            }
            for r in routines
        ]

    @staticmethod
    async def get_routine_detail(db: AsyncSession, user_id: int, routine_id: int) -> dict:
        """获取作息详情"""
        result = await db.execute(select(BabyRoutine).where(BabyRoutine.id == routine_id))
        routine = result.scalar_one_or_none()
        if not routine:
            raise NotFoundException("作息计划不存在")
        return {
            "id": routine.id,
            "baby_id": routine.baby_id,
            "template_name": routine.template_name,
            "age_month_min": routine.age_month_min,
            "age_month_max": routine.age_month_max,
            "time_slot": routine.time_slot.isoformat() if routine.time_slot else None,
            "activity_type": routine.activity_type,
            "activity_name": routine.activity_name,
            "duration_min": routine.duration_min,
            "reminder_enabled": routine.reminder_enabled,
            "reminder_before_min": routine.reminder_before_min,
            "is_auto_adjusted": routine.is_auto_adjusted,
            "adjust_reason": routine.adjust_reason,
            "effective_date": routine.effective_date.isoformat() if routine.effective_date else None,
            "expire_date": routine.expire_date.isoformat() if routine.expire_date else None,
            "is_active": routine.is_active,
            "created_at": routine.created_at.isoformat() if routine.created_at else None,
        }

    @staticmethod
    async def update_routine(db: AsyncSession, user_id: int, routine_id: int, **kwargs) -> None:
        """更新作息计划"""
        result = await db.execute(select(BabyRoutine).where(BabyRoutine.id == routine_id))
        routine = result.scalar_one_or_none()
        if not routine:
            raise NotFoundException("作息计划不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(routine, key):
                setattr(routine, key, value)

    @staticmethod
    async def delete_routine(db: AsyncSession, user_id: int, routine_id: int) -> None:
        """删除作息计划"""
        result = await db.execute(select(BabyRoutine).where(BabyRoutine.id == routine_id))
        routine = result.scalar_one_or_none()
        if not routine:
            raise NotFoundException("作息计划不存在")
        routine.is_active = 0

    @staticmethod
    async def get_conflicts(db: AsyncSession, user_id: int, baby_id: int) -> list[dict]:
        """查询作息冲突"""
        query = select(RoutineConflictLog).where(RoutineConflictLog.baby_id == baby_id)
        query = query.order_by(desc(RoutineConflictLog.conflict_date))
        result = await db.execute(query)
        conflicts = result.scalars().all()
        return [
            {
                "id": c.id,
                "baby_id": c.baby_id,
                "routine_id": c.routine_id,
                "conflict_date": c.conflict_date.isoformat() if c.conflict_date else None,
                "expected_time": c.expected_time.isoformat() if c.expected_time else None,
                "actual_time": c.actual_time.isoformat() if c.actual_time else None,
                "deviation_min": c.deviation_min,
                "conflict_type": c.conflict_type,
                "audit_analysis": c.audit_analysis,
                "suggested_fix": c.suggested_fix,
                "auto_fixed": c.auto_fixed,
            }
            for c in conflicts
        ]

    @staticmethod
    async def get_optimization(db: AsyncSession, user_id: int, baby_id: int) -> dict:
        """获取作息优化建议"""
        # 查询最近的冲突记录作为优化依据
        query = select(RoutineConflictLog).where(
            RoutineConflictLog.baby_id == baby_id,
            RoutineConflictLog.auto_fixed == 0,
        ).order_by(desc(RoutineConflictLog.conflict_date)).limit(5)
        result = await db.execute(query)
        conflicts = result.scalars().all()

        suggestions = []
        for c in conflicts:
            if c.suggested_fix:
                suggestions.append({
                    "conflict_date": c.conflict_date.isoformat() if c.conflict_date else None,
                    "conflict_type": c.conflict_type,
                    "suggestion": c.suggested_fix,
                })

        return {
            "baby_id": baby_id,
            "suggestions": suggestions,
            "total_unresolved": len([c for c in conflicts if c.auto_fixed == 0]),
        }

    @staticmethod
    async def get_today_routines(db: AsyncSession, user_id: int, baby_id: int) -> list[dict]:
        """获取今日作息安排"""
        today = date.today()
        query = select(BabyRoutine).where(
            BabyRoutine.baby_id == baby_id,
            BabyRoutine.is_active == 1,
            BabyRoutine.effective_date <= today,
        ).order_by(BabyRoutine.time_slot)
        result = await db.execute(query)
        routines = result.scalars().all()
        return [
            {
                "id": r.id,
                "template_name": r.template_name,
                "time_slot": r.time_slot.isoformat() if r.time_slot else None,
                "activity_type": r.activity_type,
                "activity_name": r.activity_name,
                "duration_min": r.duration_min,
                "reminder_enabled": r.reminder_enabled,
                "reminder_before_min": r.reminder_before_min,
                "is_auto_adjusted": r.is_auto_adjusted,
            }
            for r in routines
        ]

    # ========== EASY模式作息引导 (2.3) ==========
    @staticmethod
    async def get_easy_template(db: AsyncSession, user_id: int, baby_id: int, age_month: int) -> dict:
        """获取EASY模式模板"""
        # TODO: 根据月龄返回对应的EASY模板
        # EASY模式: Eat -> Activity -> Sleep -> You
        templates = {
            0: [  # 新生儿
                {"time_slot": "07:00", "activity_type": "Eat", "activity_name": "喂奶", "duration_min": 30},
                {"time_slot": "07:30", "activity_type": "Activity", "activity_name": "活动/换尿布", "duration_min": 30},
                {"time_slot": "08:00", "activity_type": "Sleep", "activity_name": "小睡", "duration_min": 90},
                {"time_slot": "10:00", "activity_type": "Eat", "activity_name": "喂奶", "duration_min": 30},
            ],
            6: [  # 6个月
                {"time_slot": "07:00", "activity_type": "Eat", "activity_name": "早餐", "duration_min": 30},
                {"time_slot": "08:00", "activity_type": "Activity", "activity_name": "早教游戏", "duration_min": 60},
                {"time_slot": "09:30", "activity_type": "Sleep", "activity_name": "上午小睡", "duration_min": 60},
                {"time_slot": "11:00", "activity_type": "Eat", "activity_name": "午餐", "duration_min": 30},
            ],
        }
        # 找到最接近的模板
        template_key = max([k for k in templates.keys() if k <= age_month], default=0)
        activities = templates.get(template_key, templates[0])

        return {
            "template_id": f"EASY_{age_month}m",
            "baby_id": baby_id,
            "age_month": age_month,
            "template_name": f"EASY模式-{age_month}月龄模板",
            "activities": activities,
            "cycle_days": 7,
            "created_at": datetime.now().isoformat(),
        }

    @staticmethod
    async def optimize_routine(db: AsyncSession, user_id: int, baby_id: int, analysis_days: int = 7) -> dict:
        """优化作息计划"""
        # TODO: 基于历史数据分析优化作息
        return {
            "baby_id": baby_id,
            "optimization_id": f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "current_plan": [
                {"time": "07:00", "activity": "起床/喂奶"},
                {"time": "09:30", "activity": "小睡"},
            ],
            "optimized_plan": [
                {"time": "07:30", "activity": "起床/喂奶"},
                {"time": "10:00", "activity": "小睡"},
            ],
            "changes": ["起床时间延后30分钟", "小睡时间延后30分钟"],
            "confidence_score": 0.85,
            "generated_at": datetime.now().isoformat(),
        }

    # ========== 作息冲突检测与优化 (2.4) ==========
    @staticmethod
    async def check_conflicts(db: AsyncSession, user_id: int, baby_id: int, check_days: int = 7) -> dict:
        """检测作息冲突"""
        # TODO: 基于7天历史数据检测冲突
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=check_days)

        return {
            "baby_id": baby_id,
            "check_period": f"{start_date} 至 {end_date}",
            "total_conflicts": 3,
            "conflicts": [
                {
                    "id": 1,
                    "date": (end_date - timedelta(days=1)).isoformat(),
                    "type": "sleep_delay",
                    "description": "实际入睡时间比计划晚45分钟",
                    "deviation_min": 45,
                },
                {
                    "id": 2,
                    "date": (end_date - timedelta(days=2)).isoformat(),
                    "type": "feed_early",
                    "description": "喂奶时间提前30分钟",
                    "deviation_min": 30,
                },
            ],
            "summary": "近7天共检测到3处作息偏差，主要集中在睡眠和喂养时间",
            "suggestions": ["建议延后晚间入睡时间", "调整上午小睡时长"],
            "can_auto_fix": True,
        }

    @staticmethod
    async def fix_routine(db: AsyncSession, user_id: int, baby_id: int, fix_type: str = "auto", conflict_ids: list[int] | None = None) -> dict:
        """修复作息冲突"""
        # TODO: 自动或手动修复冲突
        return {
            "baby_id": baby_id,
            "fix_type": fix_type,
            "fixed_conflicts": conflict_ids or [1, 2, 3],
            "new_schedule": [
                {"time": "07:30", "activity": "起床/喂奶"},
                {"time": "10:00", "activity": "小睡"},
                {"time": "14:00", "activity": "下午小睡"},
            ],
            "message": "作息冲突已修复，新计划已生成",
            "fixed_at": datetime.now().isoformat(),
        }


routine_service = RoutineService()
