"""
监控事件模型 - monitoring_events表
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MonitoringEvent(Base):
    """监控事件表"""

    __tablename__ = "monitoring_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    device_sn: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_level: Mapped[int] = mapped_column(server_default="0")
    trigger_source: Mapped[Optional[str]] = mapped_column(String(50), server_default="")
    breath_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    heart_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    sound_db: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    body_displace_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    pose_angle: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    screen_acted: Mapped[int] = mapped_column(server_default="0")
    sound_acted: Mapped[int] = mapped_column(server_default="0")
    app_pushed: Mapped[int] = mapped_column(server_default="0")
    parent_handled: Mapped[int] = mapped_column(server_default="0")
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    snapshot_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_clip_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    gif_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
