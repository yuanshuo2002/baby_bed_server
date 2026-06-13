"""
视频数据 Schema
"""
from datetime import datetime

from pydantic import BaseModel, Field


class VideoBase(BaseModel):
    """视频基础字段"""
    device_sn: str = Field(..., description="设备序列号")
    video_url: str = Field(..., description="视频URL地址")
    video_content_text: str = Field(..., description="视频AI理解后的文字内容")


class VideoCreate(VideoBase):
    """创建视频记录"""
    pass


class VideoUpdate(BaseModel):
    """更新视频记录"""
    video_url: str | None = Field(None, description="视频URL地址")
    video_content_text: str | None = Field(None, description="视频AI理解后的文字内容")


class VideoResponse(VideoBase):
    """视频响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
