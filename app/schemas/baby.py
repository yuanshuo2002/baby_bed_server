"""
宝宝相关Schema
"""
from datetime import date, datetime
from pydantic import BaseModel, Field


class BabyCreate(BaseModel):
    """添加宝宝请求"""
    name: str = Field(..., min_length=1, max_length=50, description="宝宝昵称")
    gender: int = Field(default=0, ge=0, le=2, description="性别：0-未知 1-男 2-女")
    birth_date: date | None = Field(None, description="出生日期")
    avatar_url: str | None = Field(None, max_length=500, description="头像URL")


class BabyUpdate(BaseModel):
    """更新宝宝信息请求"""
    name: str | None = Field(None, min_length=1, max_length=50, description="宝宝昵称")
    gender: int | None = Field(None, ge=0, le=2, description="性别")
    birth_date: date | None = Field(None, description="出生日期")
    avatar_url: str | None = Field(None, max_length=500, description="头像URL")


class BabyInfo(BaseModel):
    """宝宝信息响应"""
    id: int
    family_id: int
    name: str
    gender: int | None = None
    birth_date: date | None = None
    current_age_months: int | None = None
    avatar_url: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
