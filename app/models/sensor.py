"""
传感器原始数据模型 - sensor_data_raw表
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SensorDataRaw(Base):
    """传感器原始数据表"""

    __tablename__ = "sensor_data_raw"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_sn: Mapped[str] = mapped_column(String(64), nullable=False)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    breath_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    heart_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    body_movement: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    distance_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    sound_db: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    sound_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    pose_status: Mapped[Optional[str]] = mapped_column(
        Enum("lying", "side", "prone", "sitting", "standing"),
        nullable=True,
    )
    face_detected: Mapped[int] = mapped_column(server_default="0")
    expression: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    body_offset_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    roll_angle: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    height_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    room_temp: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    humidity: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    noise_db: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
