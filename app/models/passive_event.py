"""
被动事件类型模型 - passive_event_types表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PassiveEventType(Base):
    """被动事件类型表"""

    __tablename__ = "passive_event_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, server_default="0")
    event_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(
        Enum("sleep", "wake", "play", "cry", "danger"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(server_default="0")
    trigger_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    screen_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sound_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    app_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    is_active: Mapped[int] = mapped_column(server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
