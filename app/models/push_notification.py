"""
推送通知模型 - push_notifications表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Integer, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PushNotification(Base):
    """推送通知表"""

    __tablename__ = "push_notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    alarm_level_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    push_type: Mapped[str] = mapped_column(
        Enum("info", "warning", "alert", "emergency"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    channel_app: Mapped[int] = mapped_column(server_default="1")
    channel_sms: Mapped[int] = mapped_column(server_default="0")
    channel_call: Mapped[int] = mapped_column(server_default="0")
    channel_wechat: Mapped[int] = mapped_column(server_default="0")
    push_status: Mapped[str] = mapped_column(
        Enum("pending", "sent", "delivered", "read", "failed"),
        server_default="pending",
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, server_default="0")
    quick_actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
