"""
家庭音色库模型 - family_voice_presets表
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FamilyVoicePreset(Base):
    """家庭音色库表 - 每个家庭拥有自己的音色库"""

    __tablename__ = "family_voice_presets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="家庭ID")
    voice_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment="音色ID(唯一)")
    voice_role: Mapped[str] = mapped_column(
        Enum("mom", "dad", "nanny", "other", name="voice_role_enum"),
        nullable=False,
        comment="角色: mom/dad/nanny/other"
    )
    voice_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="音色名称")
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="音频URL")
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="音频时长(ms)")
    similarity_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True, comment="相似度评分")
    is_default: Mapped[int] = mapped_column(server_default="0", comment="是否默认音色: 0否1是")
    is_active: Mapped[int] = mapped_column(server_default="1", comment="是否有效: 0否 1是")
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", comment="排序顺序")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )