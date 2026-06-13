"""
宝宝状态日志模型 - baby_status_log表
记录宝宝状态变化：熟睡、苏醒、高兴玩耍、哭闹、危险动作
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BabyStatusLog(Base):
    """宝宝状态日志表"""

    __tablename__ = "baby_status_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    device_sn: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status_type: Mapped[str] = mapped_column(
        Enum("sleeping", "awake", "playing", "crying", "danger"),
        nullable=False,
        comment="状态类型",
    )
    status_level: Mapped[int] = mapped_column(
        Integer, 
        server_default="0", 
        comment="状态级别(哭闹1-3级)"
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="状态开始时间")
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="状态结束时间")
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="持续时长(秒)")
    
    # 触发时的传感器数据快照
    breath_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="呼吸频率")
    heart_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="心率")
    sound_db: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="声音分贝")
    pose_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="姿态")
    expression: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="表情")
    
    # 响应执行情况
    screen_triggered: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否触发屏幕响应")
    sound_triggered: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否触发声音响应")
    push_triggered: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否推送通知")
    
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
