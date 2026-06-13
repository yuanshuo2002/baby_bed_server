"""
周报相关Schema
"""
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class WeeklyReportGenerate(BaseModel):
    """生成周报请求"""
    baby_id: int = Field(..., description="宝宝ID")
    week_start: date = Field(..., description="周起始日期")
    week_end: date = Field(..., description="周结束日期")


class WeeklyReportInfo(BaseModel):
    """周报信息响应"""
    id: int
    baby_id: int
    report_week: date | None = None
    week_start: date | None = None
    week_end: date | None = None
    total_sleep_hours: Decimal | None = None
    avg_daily_sleep: Decimal | None = None
    cry_event_count: int | None = None
    danger_event_count: int | None = None
    milestone_count: int | None = None
    smile_count: int | None = None
    routine_compliance: Decimal | None = None
    summary_text: str | None = None
    growth_highlights: str | None = None
    health_notes: str | None = None
    suggestions: str | None = None
    generated_at: datetime | None = None
    llm_model: str | None = None
    push_status: int | None = None
    pushed_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
