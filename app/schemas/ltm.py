"""
长记忆(LTM) Schema
"""
from datetime import date, datetime
from typing import Any, Union

from pydantic import BaseModel, Field, field_validator


class LTMTimelineRequest(BaseModel):
    """时间轴查询请求"""
    date: Union[date, None] = None
    event_type: Union[str, None] = None
    limit: int = 100
    page: int = 1

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str) and v:
            return date.fromisoformat(v)
        return None

    model_config = {
        "json_schema_extra": {
            "date": "YYYY-MM-DD",
            "event_type": "sleeping/crying/danger/playing",
            "limit": "1-500",
        }
    }


class LTMMemoryResponse(BaseModel):
    """记忆库响应"""
    l0_events: list[dict[str, Any]] = Field(default_factory=list)
    l1_hourly: list[dict[str, Any]] = Field(default_factory=list)
    l2_daily: list[dict[str, Any]] = Field(default_factory=list)


class LTMEventUploadRequest(BaseModel):
    """事件上传请求"""
    description: str = Field(..., max_length=1000)
    profile_id: int = 1


class LTMAskRequest(BaseModel):
    """问答请求"""
    question: str = Field(..., max_length=500)
    profile_id: int = 1


class LTMBatchExtractRequest(BaseModel):
    """批量提取请求"""
    descriptions: list[str] = Field(..., min_length=1, max_length=50)
    profile_id: int = 1


class LTMEventInfo(BaseModel):
    """事件信息"""
    id: str = ""
    date: Union[str, None] = None
    start_time: Union[str, None] = None
    end_time: Union[str, None] = None
    event_type: Union[str, None] = None
    event_id: Union[str, None] = None
    emotion: Union[str, None] = None
    pose: Union[str, None] = None
    risk: Union[str, None] = None
    keywords: Union[str, None] = None
    summary: Union[str, None] = None


class LTMTimelineResponse(BaseModel):
    """时间轴响应"""
    items: list[LTMEventInfo] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class LTMAskResponse(BaseModel):
    """问答响应"""
    question: str = ""
    answer: str = ""
    related_events: list[dict[str, Any]] = Field(default_factory=list)


class LTMUploadResponse(BaseModel):
    """事件上传响应"""
    event_id: Union[str, None] = None
    message: str = "success"
    detected_type: Union[str, None] = None


class LTMScheduleRequest(BaseModel):
    """生成作息计划请求"""
    baby_id: int = Field(...)
    days: int = Field(default=7, ge=3, le=14)


class LTMScheduleResponse(BaseModel):
    """作息计划响应"""
    baby_id: int = 0
    period_start: str = ""
    period_end: str = ""
    sleep_pattern: str = ""
    feeding_pattern: Union[str, None] = None
    suggested_routine: list[dict[str, Any]] = Field(default_factory=list)
    optimization_score: float = 0.0


class LTMDailySummaryResponse(BaseModel):
    """每日摘要响应"""
    date: str = ""
    total_events: int = 0
    crying_count: int = 0
    sleeping_count: int = 0
    danger_count: int = 0
    summary_text: Union[str, None] = None