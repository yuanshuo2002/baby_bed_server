"""
视频模型 - videos 表
存储硬件端上传的视频文件信息
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Video(Base):
    """视频文件信息表"""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_sn: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="视频封面图片URL")
    video_content_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="视频AI理解后的文字内容")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
