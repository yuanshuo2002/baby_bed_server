"""
哭闹事件模型 - cry_event表
记录哭闹事件详情，支持分级分类
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CryEvent(Base):
    """哭闹事件表"""

    __tablename__ = "cry_event"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    device_sn: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # 哭闹分级
    cry_level: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment="哭闹级别: 1=轻微哼唧, 2=有节奏哭闹, 3=剧烈大哭"
    )
    
    # 哭闹分类
    cry_type: Mapped[Optional[str]] = mapped_column(
        Enum("hunger", "discomfort", "pain", "attention", "unknown"),
        nullable=True,
        comment="哭闹类型: 饥饿/不适/疼痛/求关注/未知"
    )
    
    # 时间信息
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="结束时间")
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="持续时长(秒)")
    
    # 触发数据
    sound_db: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="声音分贝")
    heart_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="心率")
    body_movement: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, comment="体动活跃度")
    expression: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="表情")
    
    # 响应执行
    lullaby_played: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否播放摇篮曲")
    voice_played: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否播放父母语音")
    parent_notified: Mapped[int] = mapped_column(Integer, server_default="0", comment="是否通知父母")
    
    # 处理结果
    parent_handled: Mapped[int] = mapped_column(Integer, server_default="0", comment="父母是否处理")
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="处理时间")
    handle_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="处理方式")
    
    snapshot_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="快照图片URL")
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="视频片段URL")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
