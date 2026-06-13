"""
宝宝管理业务逻辑层
"""
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.baby import Baby
from app.models.family_member import FamilyMember
from app.services.family_service import FamilyService


class BabyService:
    """宝宝管理服务"""

    @staticmethod
    async def add_baby(db: AsyncSession, user_id: int, **kwargs) -> dict:
        """添加宝宝"""
        family = await FamilyService._get_user_family_obj(db, user_id)

        baby = Baby(family_id=family.id, **kwargs)
        db.add(baby)
        await db.flush()

        return {
            "id": baby.id,
            "family_id": baby.family_id,
            "name": baby.name,
            "gender": baby.gender,
            "birth_date": baby.birth_date.isoformat() if baby.birth_date else None,
            "avatar_url": baby.avatar_url,
        }

    @staticmethod
    async def get_baby_list(db: AsyncSession, user_id: int) -> list[dict]:
        """获取宝宝列表"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(select(Baby).where(Baby.family_id == family.id))
        babies = result.scalars().all()
        return [
            {
                "id": b.id,
                "family_id": b.family_id,
                "name": b.name,
                "gender": b.gender,
                "birth_date": b.birth_date.isoformat() if b.birth_date else None,
                "current_age_months": b.current_age_months,
                "avatar_url": b.avatar_url,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in babies
        ]

    @staticmethod
    async def get_baby_detail(db: AsyncSession, user_id: int, baby_id: int) -> dict:
        """获取宝宝详情"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(select(Baby).where(Baby.id == baby_id, Baby.family_id == family.id))
        baby = result.scalar_one_or_none()
        if not baby:
            raise NotFoundException("宝宝不存在")
        return {
            "id": baby.id,
            "family_id": baby.family_id,
            "name": baby.name,
            "gender": baby.gender,
            "birth_date": baby.birth_date.isoformat() if baby.birth_date else None,
            "current_age_months": baby.current_age_months,
            "avatar_url": baby.avatar_url,
            "created_at": baby.created_at.isoformat() if baby.created_at else None,
        }

    @staticmethod
    async def update_baby(db: AsyncSession, user_id: int, baby_id: int, **kwargs) -> None:
        """更新宝宝信息"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(select(Baby).where(Baby.id == baby_id, Baby.family_id == family.id))
        baby = result.scalar_one_or_none()
        if not baby:
            raise NotFoundException("宝宝不存在")

        for key, value in kwargs.items():
            if value is not None and hasattr(baby, key):
                setattr(baby, key, value)

    @staticmethod
    async def delete_baby(db: AsyncSession, user_id: int, baby_id: int) -> None:
        """删除宝宝"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(select(Baby).where(Baby.id == baby_id, Baby.family_id == family.id))
        baby = result.scalar_one_or_none()
        if not baby:
            raise NotFoundException("宝宝不存在")
        await db.delete(baby)


baby_service = BabyService()
