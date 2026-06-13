"""
成长里程碑模型 - growth_milestones表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GrowthMilestone(Base):
    """成长里程碑表"""

    __tablename__ = "growth_milestones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    milestone_code: Mapped[str] = mapped_column(String(50), nullable=False)
    milestone_name: Mapped[str] = mapped_column(String(100), nullable=False)
    milestone_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    age_months: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    snapshot_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    gif_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_clip_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    gif_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_highlight: Mapped[int] = mapped_column(server_default="1")
    week_report_included: Mapped[int] = mapped_column(server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
