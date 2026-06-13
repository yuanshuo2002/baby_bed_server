from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.baby import Baby
from app.models.push_notification import PushNotification
from app.services.family_service import FamilyService


class PushService:
    _settings: dict[int, dict] = {}

    @classmethod
    def get_settings(cls, user_id: int) -> dict:
        return cls._settings.get(user_id, {"channel_app": True, "channel_sms": False, "quiet_hours": None})

    @classmethod
    def update_settings(cls, user_id: int, **kwargs) -> dict:
        cls._settings[user_id] = kwargs
        return kwargs

    @staticmethod
    async def get_history(db: AsyncSession, user_id: int, page: int, page_size: int) -> dict:
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(select(Baby.id).where(Baby.family_id == family.id))
        baby_ids = [row[0] for row in result.all()]
        if not baby_ids:
            return {"items": [], "page": page, "page_size": page_size}
        result = await db.execute(
            select(PushNotification)
            .where(PushNotification.baby_id.in_(baby_ids))
            .order_by(desc(PushNotification.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return {
            "items": [
                {
                    "id": item.id, "baby_id": item.baby_id, "push_type": item.push_type,
                    "title": item.title, "content": item.content, "push_status": item.push_status,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in result.scalars().all()
            ],
            "page": page,
            "page_size": page_size,
        }


push_service = PushService()
