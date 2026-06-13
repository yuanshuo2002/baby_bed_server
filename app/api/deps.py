"""
公共依赖模块
提供认证、数据库会话等公共依赖注入
"""
from collections.abc import AsyncGenerator

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import verify_token
from app.database import get_db
from app.models.user import User


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async for session in get_db():
        yield session


async def get_current_user(
    authorization: str = Header(..., description="Bearer Token"),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    获取当前登录用户
    从请求头中提取JWT Token并验证，返回用户对象

    Args:
        authorization: 请求头中的Authorization字段，格式为 Bearer {token}
        db: 数据库会话

    Returns:
        当前登录的用户对象

    Raises:
        UnauthorizedException: Token无效或用户不存在
    """
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException("Token格式错误")

    token = authorization.replace("Bearer ", "").strip()
    payload = verify_token(token)

    if payload is None:
        raise UnauthorizedException("Token无效或已过期")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Token中缺少用户标识")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("用户不存在")

    if user.status != "active":
        raise UnauthorizedException("用户已被禁用")

    return user


async def get_current_user_id(
    current_user: User = Depends(get_current_user),
) -> int:
    """
    获取当前登录用户ID
    便捷依赖，仅返回用户ID

    Args:
        current_user: 当前用户对象

    Returns:
        用户ID
    """
    return current_user.id
