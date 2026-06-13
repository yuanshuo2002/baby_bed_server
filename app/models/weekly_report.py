"""
AI周报模型 - ai_weekly_reports表
支持日报、周报、月报
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIWeeklyReport(Base):
    """AI成长报告表（支持日报、周报、月报）"""

    __tablename__ = "ai_weekly_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    report_type: Mapped[str] = mapped_column(String(10), nullable=False, default="weekly")  # daily/weekly/monthly
    period_start: Mapped[date] = mapped_column(Date, nullable=False, comment="周期开始日期")
    period_end: Mapped[date] = mapped_column(Date, nullable=False, comment="周期结束日期")
    total_sleep_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    avg_daily_sleep: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    cry_event_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    danger_event_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    milestone_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    smile_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    routine_compliance: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    summary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    growth_highlights: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    health_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggestions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    push_status: Mapped[int] = mapped_column(server_default="0")
    pushed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
