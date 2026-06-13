"""
家庭模型 - families表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Family(Base):
    """家庭表"""

    __tablename__ = "families"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    family_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    family_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    plan_type: Mapped[str] = mapped_column(
        Enum("free", "basic", "premium"),
        server_default="free",
    )
    plan_expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    device_quota: Mapped[int] = mapped_column(Integer, server_default="1")
    baby_quota: Mapped[int] = mapped_column(Integer, server_default="1")
    status: Mapped[str] = mapped_column(
        Enum("active", "suspended", "deleted"),
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
