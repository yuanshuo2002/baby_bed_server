"""
设备模型 - devices表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Device(Base):
    """设备表"""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_sn: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    baby_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    device_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    device_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    work_mode: Mapped[str] = mapped_column(
        Enum("sleep", "play", "co_sleep"),
        server_default="sleep",
    )
    online_status: Mapped[int] = mapped_column(server_default="0")
    last_online_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
