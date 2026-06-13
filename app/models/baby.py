"""
宝宝模型 - babies表
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, SmallInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Baby(Base):
    """宝宝表"""

    __tablename__ = "babies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[Optional[int]] = mapped_column(server_default="0")
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    current_age_months: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
