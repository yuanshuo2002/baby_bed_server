"""
家庭成员模型 - family_members表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FamilyMember(Base):
    """家庭成员表"""

    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    family_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    member_role: Mapped[str] = mapped_column(
        Enum("parent", "grandparent", "nanny", "other"),
        server_default="parent",
    )
    relation: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    can_view: Mapped[int] = mapped_column(server_default="1")
    can_control: Mapped[int] = mapped_column(server_default="1")
    can_receive_push: Mapped[int] = mapped_column(server_default="1")
    push_priority: Mapped[int] = mapped_column(server_default="0")
    is_emergency_contact: Mapped[int] = mapped_column(server_default="0")
    is_active: Mapped[int] = mapped_column(server_default="1")
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
