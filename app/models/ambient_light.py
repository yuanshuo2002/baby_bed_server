"""
环境灯光配置模型 - ambient_light_configs表
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AmbientLightConfig(Base):
    """环境灯光配置表"""

    __tablename__ = "ambient_light_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    alarm_level_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    light_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    color_primary: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    color_secondary: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    brightness_pct: Mapped[int] = mapped_column(server_default="100")
    blink_enabled: Mapped[int] = mapped_column(server_default="0")
    blink_freq_hz: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1), nullable=True)
    gradient_enabled: Mapped[int] = mapped_column(server_default="0")
    gradient_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[int] = mapped_column(server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
