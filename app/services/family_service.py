"""
家庭管理业务逻辑层
"""
import random
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ForbiddenException
from app.models.baby import Baby
from app.models.conversation import ConversationContext
from app.models.cry_event import CryEvent
from app.models.danger_event import DangerEvent
from app.models.device import Device
from app.models.device_mode import DeviceModeSwitch
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.family_voice_preset import FamilyVoicePreset
from app.models.milestone import GrowthMilestone
from app.models.monitoring import MonitoringEvent
from app.models.push_notification import PushNotification
from app.models.routine import BabyRoutine
from app.models.routine_conflict import RoutineConflictLog
from app.models.sensor import SensorDataRaw
from app.models.sleep_report import SleepReport
from app.models.status_log import BabyStatusLog
from app.models.user import User
from app.models.voice_clip import ParentVoiceClip
from app.models.weekly_report import AIWeeklyReport


def _generate_family_code(length: int = 8) -> str:
    """生成家庭邀请码"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


class FamilyService:
    """家庭管理服务"""

    @staticmethod
    async def create_family(db: AsyncSession, user_id: int, family_name: str) -> dict:
        """创建家庭"""
        # 检查用户是否已有家庭
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.user_id == user_id, FamilyMember.is_active == 1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ConflictException("您已加入一个家庭，请先退出当前家庭")

        # 生成唯一邀请码
        family_code = _generate_family_code()
        for _ in range(10):
            result = await db.execute(select(Family).where(Family.family_code == family_code))
            if not result.scalar_one_or_none():
                break
            family_code = _generate_family_code()

        # 创建家庭
        family = Family(family_name=family_name, family_code=family_code)
        db.add(family)
        await db.flush()

        # 创建者自动加入
        member = FamilyMember(
            family_id=family.id,
            user_id=user_id,
            member_role="parent",
            relation="creator",
            display_name="创建者",
        )
        db.add(member)
        await db.flush()

        return {
            "id": family.id,
            "family_name": family.family_name,
            "family_code": family.family_code,
        }

    @staticmethod
    async def join_family(
        db: AsyncSession, user_id: int, family_code: str,
        member_role: str = "parent", relation: str | None = None,
        display_name: str | None = None,
    ) -> dict:
        """加入家庭"""
        # 查找家庭
        result = await db.execute(select(Family).where(Family.family_code == family_code, Family.status == "active"))
        family = result.scalar_one_or_none()
        if not family:
            raise NotFoundException("邀请码无效或家庭不存在")

        # 检查是否已加入
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.family_id == family.id, FamilyMember.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing and existing.is_active:
            raise ConflictException("您已在该家庭中")
        if existing:
            existing.is_active = 1
            existing.member_role = member_role
            existing.relation = relation
            existing.display_name = display_name
            return {"id": family.id, "family_name": family.family_name, "message": "加入成功"}

        # 加入家庭
        member = FamilyMember(
            family_id=family.id,
            user_id=user_id,
            member_role=member_role,
            relation=relation,
            display_name=display_name,
        )
        db.add(member)
        await db.flush()

        return {"id": family.id, "family_name": family.family_name, "message": "加入成功"}

    @staticmethod
    async def get_user_family(db: AsyncSession, user_id: int) -> dict | None:
        """获取用户所在家庭信息"""
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.user_id == user_id, FamilyMember.is_active == 1)
        )
        member = result.scalar_one_or_none()
        if not member:
            return None

        result = await db.execute(select(Family).where(Family.id == member.family_id))
        family = result.scalar_one_or_none()
        if not family:
            return None

        return {
            "id": family.id,
            "family_name": family.family_name,
            "family_code": family.family_code,
            "plan_type": family.plan_type,
            "device_quota": family.device_quota,
            "baby_quota": family.baby_quota,
            "status": family.status,
            "created_at": family.created_at.isoformat() if family.created_at else None,
        }

    @staticmethod
    async def update_family_info(db: AsyncSession, user_id: int, family_name: str | None) -> dict:
        """更新家庭信息"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        if family_name:
            family.family_name = family_name
        return {"id": family.id, "family_name": family.family_name}

    @staticmethod
    async def get_family_members(db: AsyncSession, user_id: int) -> list[dict]:
        """获取家庭成员列表"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.family_id == family.id, FamilyMember.is_active == 1)
        )
        members = result.scalars().all()
        member_list = []
        for m in members:
            # 查询用户信息
            user_result = await db.execute(select(User).where(User.id == m.user_id))
            user = user_result.scalar_one_or_none()
            member_list.append({
                "id": m.id,
                "user_id": m.user_id,
                "member_role": m.member_role,
                "is_admin": m.relation == "creator",
                "relation": m.relation,
                "display_name": m.display_name,
                "phone": m.phone,
                "can_view": m.can_view,
                "can_control": m.can_control,
                "can_receive_push": m.can_receive_push,
                "is_emergency_contact": m.is_emergency_contact,
                "nickname": user.nickname if user else None,
                "avatar_url": user.avatar_url if user else None,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            })
        return member_list

    @staticmethod
    async def get_invite_code(db: AsyncSession, user_id: int) -> dict:
        """获取邀请码"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        return {"family_code": family.family_code}

    @staticmethod
    async def leave_family(db: AsyncSession, user_id: int) -> None:
        """退出家庭"""
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.user_id == user_id, FamilyMember.is_active == 1)
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundException("您未加入任何家庭")
        if member.relation == "creator":
            raise ForbiddenException("管理员须先转让管理员才能离开家庭")
        member.is_active = 0

    @staticmethod
    async def regenerate_invite_code(db: AsyncSession, user_id: int) -> dict:
        family, _ = await FamilyService._get_admin_context(db, user_id)
        family.family_code = _generate_family_code()
        return {"family_code": family.family_code}

    @staticmethod
    async def transfer_admin(db: AsyncSession, user_id: int, member_id: int) -> None:
        family, admin = await FamilyService._get_admin_context(db, user_id)
        result = await db.execute(select(FamilyMember).where(FamilyMember.id == member_id, FamilyMember.family_id == family.id, FamilyMember.is_active == 1))
        target = result.scalar_one_or_none()
        if not target:
            raise NotFoundException("家庭成员不存在")
        admin.relation = None if admin.relation == "creator" else admin.relation
        target.relation = "creator"

    @staticmethod
    async def dissolve_family(db: AsyncSession, user_id: int) -> None:
        family, _ = await FamilyService._get_admin_context(db, user_id)
        family_id = family.id

        # 1. 删除家庭成员
        members_result = await db.execute(
            select(FamilyMember).where(FamilyMember.family_id == family_id)
        )
        for member in members_result.scalars().all():
            await db.delete(member)

        # 2. 删除家庭音色库
        presets_result = await db.execute(
            select(FamilyVoicePreset).where(FamilyVoicePreset.family_id == family_id)
        )
        for preset in presets_result.scalars().all():
            await db.delete(preset)

        # 3. 删除家长语音片段
        clips_result = await db.execute(
            select(ParentVoiceClip).where(ParentVoiceClip.family_id == family_id)
        )
        for clip in clips_result.scalars().all():
            await db.delete(clip)

        # 4. 查询所有宝宝，获取 baby_id 列表
        babies_result = await db.execute(select(Baby).where(Baby.family_id == family_id))
        babies = babies_result.scalars().all()
        baby_ids = [baby.id for baby in babies]

        # 5. 级联删除所有宝宝相关数据
        if baby_ids:
            # 状态日志
            for baby_id in baby_ids:
                result = await db.execute(select(BabyStatusLog).where(BabyStatusLog.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 哭闹事件
                result = await db.execute(select(CryEvent).where(CryEvent.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 危险事件
                result = await db.execute(select(DangerEvent).where(DangerEvent.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 监控事件
                result = await db.execute(select(MonitoringEvent).where(MonitoringEvent.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 对话上下文
                result = await db.execute(select(ConversationContext).where(ConversationContext.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 成长里程碑
                result = await db.execute(select(GrowthMilestone).where(GrowthMilestone.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 宝宝作息
                result = await db.execute(select(BabyRoutine).where(BabyRoutine.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 推送通知
                result = await db.execute(select(PushNotification).where(PushNotification.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # AI周报
                result = await db.execute(select(AIWeeklyReport).where(AIWeeklyReport.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 睡眠报告
                result = await db.execute(select(SleepReport).where(SleepReport.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 作息冲突日志
                result = await db.execute(select(RoutineConflictLog).where(RoutineConflictLog.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 传感器原始数据
                result = await db.execute(select(SensorDataRaw).where(SensorDataRaw.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 设备模式切换
                result = await db.execute(select(DeviceModeSwitch).where(DeviceModeSwitch.baby_id == baby_id))
                for record in result.scalars().all():
                    await db.delete(record)

                # 设备（通过 baby_id）- 解除绑定，不删除设备记录
                result = await db.execute(select(Device).where(Device.baby_id == baby_id))
                for record in result.scalars().all():
                    record.baby_id = None

        # 6. 删除宝宝
        for baby in babies:
            await db.delete(baby)

        # 7. 删除家庭
        await db.delete(family)

    @staticmethod
    async def update_member_role(db: AsyncSession, user_id: int, member_id: int, member_role: str) -> None:
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(select(FamilyMember).where(FamilyMember.id == member_id, FamilyMember.family_id == family.id, FamilyMember.is_active == 1))
        target = result.scalar_one_or_none()
        if not target:
            raise NotFoundException("家庭成员不存在")
        if target.user_id != user_id:
            await FamilyService._get_admin_context(db, user_id)
        target.member_role = member_role

    @staticmethod
    async def remove_member(db: AsyncSession, user_id: int, member_id: int) -> None:
        family, _ = await FamilyService._get_admin_context(db, user_id)
        result = await db.execute(select(FamilyMember).where(FamilyMember.id == member_id, FamilyMember.family_id == family.id, FamilyMember.is_active == 1))
        target = result.scalar_one_or_none()
        if not target:
            raise NotFoundException("家庭成员不存在")
        if target.user_id == user_id:
            raise ForbiddenException("管理员不能移除自己，请先转让管理员")
        target.is_active = 0

    @staticmethod
    async def _get_admin_context(db: AsyncSession, user_id: int) -> tuple[Family, FamilyMember]:
        result = await db.execute(select(FamilyMember).where(FamilyMember.user_id == user_id, FamilyMember.is_active == 1))
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundException("您未加入任何家庭")
        if member.relation != "creator":
            raise ForbiddenException("仅家庭管理员可执行此操作")
        result = await db.execute(select(Family).where(Family.id == member.family_id, Family.status == "active"))
        family = result.scalar_one_or_none()
        if not family:
            raise NotFoundException("家庭不存在")
        return family, member

    @staticmethod
    async def _get_user_family_obj(db: AsyncSession, user_id: int) -> Family:
        """获取用户所在家庭对象"""
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.user_id == user_id, FamilyMember.is_active == 1)
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundException("您未加入任何家庭")

        result = await db.execute(select(Family).where(Family.id == member.family_id))
        family = result.scalar_one_or_none()
        if not family:
            raise NotFoundException("家庭不存在")
        return family


family_service = FamilyService()
