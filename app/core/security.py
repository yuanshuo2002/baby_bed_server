"""
JWT认证工具模块
提供 Token 创建、验证和解析功能
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from config import settings


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    创建JWT访问令牌

    Args:
        data: 要编码到令牌中的数据（通常包含sub字段为用户ID）
        expires_delta: 令牌有效期，默认使用配置中的值

    Returns:
        编码后的JWT令牌字符串
    """
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str) -> dict | None:
    """
    验证JWT令牌并返回载荷数据

    Args:
        token: 待验证的JWT令牌字符串

    Returns:
        令牌载荷字典，验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> dict | None:
    """
    解码JWT令牌（不验证过期时间）

    Args:
        token: 待解码的JWT令牌字符串

    Returns:
        令牌载荷字典，解码失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        return payload
    except JWTError:
        return None
