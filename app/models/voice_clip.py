"""
家长语音片段模型 - parent_voice_clips表
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ParentVoiceClip(Base):
    """家长语音片段表"""

    __tablename__ = "parent_voice_clips"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    voice_role: Mapped[str] = mapped_column(
        Enum("mom", "dad", "nanny", "other"),
        nullable=False,
    )
    clip_type: Mapped[str] = mapped_column(
        Enum("clone_sample", "preset", "custom"),
        nullable=False,
    )
    clip_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_type_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scenario: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tts_model_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    similarity_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    is_active: Mapped[int] = mapped_column(server_default="1")
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
