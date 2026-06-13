"""
婴儿互动Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class InteractionContentRequest(BaseModel):
    """互动内容请求"""
    baby_id: int = Field(..., description="宝宝ID")
    content_type: str = Field(..., description="内容类型: music/song/rhyme/story/game/exercise")
    content_name: str = Field(..., max_length=100, description="内容名称")
    content_data: Optional[str] = Field(None, description="内容数据(JSON)")


class InteractionHistoryRecord(BaseModel):
    """互动历史记录请求"""
    baby_id: int = Field(..., description="宝宝ID")
    content_id: int = Field(..., description="内容ID")
    interaction_type: str = Field(..., description="互动类型: play/like/complete")
    duration_sec: int = Field(0, description="持续时长(秒)")
    engagement_score: float = Field(0, description="参与度评分")