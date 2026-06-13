"""
告警等级模型 - alarm_levels表
"""
from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AlarmLevel(Base):
    """告警等级表"""

    __tablename__ = "alarm_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    level_name: Mapped[str] = mapped_column(String(50), nullable=False)
    level_value: Mapped[int] = mapped_column(nullable=False)
    screen_behavior: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    sound_behavior: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    app_behavior: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    push_enabled: Mapped[int] = mapped_column(server_default="1")
    push_vibrate: Mapped[int] = mapped_column(server_default="0")
    push_sound_max: Mapped[int] = mapped_column(server_default="0")
    auto_call: Mapped[int] = mapped_column(server_default="0")
    auto_record: Mapped[int] = mapped_column(server_default="0")
    record_before_sec: Mapped[int] = mapped_column(Integer, server_default="15")
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
