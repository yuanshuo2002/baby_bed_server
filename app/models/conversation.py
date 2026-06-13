"""
对话上下文模型 - conversation_contexts表
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConversationContext(Base):
    """对话上下文表"""

    __tablename__ = "conversation_contexts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("user", "assistant", "system"),
        nullable=False,
    )
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    ltm_tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_ltm_stored: Mapped[int] = mapped_column(server_default="0")
    ltm_importance: Mapped[int] = mapped_column(server_default="0")
    asr_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    tts_voice_role: Mapped[Optional[str]] = mapped_column(
        Enum("mom", "dad", "nanny", "other"),
        nullable=True,
    )
    tts_model_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    response_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
