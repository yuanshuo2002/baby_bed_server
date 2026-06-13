"""
屏幕动画相关 Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnimationCreate(BaseModel):
    """创建动画配置"""
    event_type_id: int = Field(..., description="事件类型ID")
    animation_name: str = Field(..., max_length=100, description="动画名称")
    animation_desc: Optional[str] = Field(None, description="动画描述")
    animation_url: str = Field(..., max_length=500, description="动画资源URL")
    duration_ms: int = Field(..., gt=0, description="动画持续时间(毫秒)")
    file_size_bytes: Optional[int] = Field(None, gt=0, description="文件大小(字节)")
    screen_mode: str = Field(
        default="dim",
        description="屏幕模式: off/dim/warm/bright/alert_red/alert_orange"
    )
    bg_color: Optional[str] = Field(None, max_length=20, description="背景颜色")
    text_overlay: Optional[str] = Field(None, max_length=200, description="文字叠加")


class AnimationUpdate(BaseModel):
    """更新动画配置"""
    event_type_id: Optional[int] = Field(None, description="事件类型ID")
    animation_name: Optional[str] = Field(None, max_length=100, description="动画名称")
    animation_desc: Optional[str] = Field(None, description="动画描述")
    animation_url: Optional[str] = Field(None, max_length=500, description="动画资源URL")
    duration_ms: Optional[int] = Field(None, gt=0, description="动画持续时间(毫秒)")
    file_size_bytes: Optional[int] = Field(None, gt=0, description="文件大小(字节)")
    screen_mode: Optional[str] = Field(None, description="屏幕模式")
    bg_color: Optional[str] = Field(None, max_length=20, description="背景颜色")
    text_overlay: Optional[str] = Field(None, max_length=200, description="文字叠加")
    is_active: Optional[int] = Field(None, description="是否启用")


class AnimationResponse(BaseModel):
    """动画响应"""
    id: int
    event_type_id: int
    animation_name: str
    animation_desc: Optional[str]
    animation_url: str
    duration_ms: int
    file_size_bytes: Optional[int]
    screen_mode: str
    bg_color: Optional[str]
    text_overlay: Optional[str]
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True