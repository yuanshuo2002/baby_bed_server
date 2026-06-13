"""
用户模型 - users表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gender: Mapped[Optional[int]] = mapped_column(server_default="0")
    wechat_openid: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    wechat_unionid: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    device_token: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", "banned"),
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
