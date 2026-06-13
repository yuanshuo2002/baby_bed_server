"""
宝宝作息模型 - baby_routines表
"""
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, Enum, Integer, SmallInteger, String, Time, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BabyRoutine(Base):
    """宝宝作息表"""

    __tablename__ = "baby_routines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_name: Mapped[str] = mapped_column(String(50), nullable=False)
    age_month_min: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    age_month_max: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    time_slot: Mapped[time] = mapped_column(Time, nullable=False)
    activity_type: Mapped[str] = mapped_column(
        Enum("eat", "active", "sleep", "y"),
        nullable=False,
    )
    activity_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reminder_enabled: Mapped[int] = mapped_column(server_default="1")
    reminder_before_min: Mapped[int] = mapped_column(Integer, server_default="10")
    is_auto_adjusted: Mapped[int] = mapped_column(server_default="0")
    adjust_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[int] = mapped_column(server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
