"""
设备模式切换模型 - device_mode_switches表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeviceModeSwitch(Base):
    """设备模式切换表"""

    __tablename__ = "device_mode_switches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_sn: Mapped[str] = mapped_column(String(64), nullable=False)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_mode: Mapped[Optional[str]] = mapped_column(
        Enum("sleep", "play", "co_sleep"),
        nullable=True,
    )
    to_mode: Mapped[str] = mapped_column(
        Enum("sleep", "play", "co_sleep"),
        nullable=False,
    )
    switch_type: Mapped[str] = mapped_column(
        Enum("manual", "auto"),
        server_default="manual",
    )
    switch_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    alarm_enabled: Mapped[int] = mapped_column(server_default="1")
    monitor_sensitivity: Mapped[str] = mapped_column(
        Enum("low", "medium", "high"),
        server_default="medium",
    )
    switched_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
