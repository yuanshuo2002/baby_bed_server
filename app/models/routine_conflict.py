"""
作息冲突日志模型 - routine_conflict_logs表
"""
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, Enum, Integer, String, Text, Time, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RoutineConflictLog(Base):
    """作息冲突日志表"""

    __tablename__ = "routine_conflict_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    routine_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    conflict_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    actual_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    deviation_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    conflict_type: Mapped[Optional[str]] = mapped_column(
        Enum("sleep_overrun", "feed_delay", "wake_early", "missed_nap", "other"),
        nullable=True,
    )
    audit_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_fix: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auto_fixed: Mapped[int] = mapped_column(server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
