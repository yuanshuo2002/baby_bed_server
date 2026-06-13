"""
屏幕动画模型 - screen_animations表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScreenAnimation(Base):
    """屏幕动画表"""

    __tablename__ = "screen_animations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    animation_name: Mapped[str] = mapped_column(String(100), nullable=False)
    animation_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    animation_url: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    screen_mode: Mapped[str] = mapped_column(
        Enum("off", "dim", "warm", "bright", "alert_red", "alert_orange"),
        server_default="dim",
    )
    bg_color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    text_overlay: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[int] = mapped_column(server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
