"""
用户业务逻辑层
处理用户配置、主题设置等
"""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.user import User


class UserService:
    """用户服务"""

    @staticmethod
    async def get_theme_config(db: AsyncSession, user_id: int) -> dict:
        """获取用户主题配置"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("用户不存在")

        # 返回默认配置或用户自定义配置
        return {
            "user_id": user_id,
            "theme_name": "warm",
            "primary_color": "#667eea",
            "font_size": "medium",
            "animation_enabled": True,
            "updated_at": datetime.now().isoformat(),
        }

    @staticmethod
    async def update_theme_config(
        db: AsyncSession, user_id: int,
        theme_name: str = "warm", primary_color: str | None = None,
        font_size: str = "medium", animation_enabled: bool = True,
    ) -> dict:
        """更新用户主题配置"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("用户不存在")

        # TODO: 存储用户配置到数据库
        return {
            "user_id": user_id,
            "theme_name": theme_name,
            "primary_color": primary_color,
            "font_size": font_size,
            "animation_enabled": animation_enabled,
            "updated_at": datetime.now().isoformat(),
        }


user_service = UserService()
