"""
里程碑相关Schema
"""
from datetime import date, datetime
from pydantic import BaseModel, Field


class MilestoneCreate(BaseModel):
    """创建里程碑请求"""
    baby_id: int = Field(..., description="宝宝ID")
    event_type_id: int = Field(..., description="事件类型ID")
    milestone_code: str = Field(..., max_length=50, description="里程碑编码")
    milestone_name: str = Field(..., min_length=1, max_length=100, description="里程碑名称")
    milestone_desc: str | None = Field(None, description="描述")
    age_months: int | None = Field(None, description="发生时月龄")
    snapshot_url: str | None = Field(None, max_length=500, description="抓拍图片URL")
    gif_url: str | None = Field(None, max_length=500, description="GIF URL")
    video_clip_url: str | None = Field(None, max_length=500, description="视频URL")
    detected_at: datetime = Field(..., description="检测时间")


class MilestoneInfo(BaseModel):
    """里程碑信息响应"""
    id: int
    baby_id: int
    event_type_id: int
    milestone_code: str
    milestone_name: str
    milestone_desc: str | None = None
    age_months: int | None = None
    snapshot_url: str | None = None
    gif_url: str | None = None
    video_clip_url: str | None = None
    gif_size_bytes: int | None = None
    detected_at: datetime | None = None
    is_highlight: int | None = None
    week_report_included: int | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ========== 关键事件自动固化 (3.2) ==========
class EventCaptureRequest(BaseModel):
    """事件视频截取请求"""
    baby_id: int = Field(..., description="宝宝ID")
    event_type: str = Field(..., description="事件类型: smile/sit/turn_over/...")
    trigger_time: datetime = Field(..., description="触发时间")
    pre_seconds: int = Field(default=3, ge=1, le=10, description="触发前截取秒数")
    post_seconds: int = Field(default=5, ge=1, le=10, description="触发后截取秒数")


class EventCaptureResponse(BaseModel):
    """事件视频截取响应"""
    capture_id: str
    baby_id: int
    event_type: str
    video_url: str = Field(..., description="视频片段URL")
    gif_url: str | None = Field(None, description="GIF动图URL")
    gif_size_bytes: int | None = Field(None, description="GIF大小(字节), 要求<2MB")
    duration_sec: int = Field(..., description="总时长(秒)")
    status: str = Field(..., description="生成状态: processing/completed/failed")
    created_at: datetime | None = None


class GIFGenerateRequest(BaseModel):
    """GIF生成请求"""
    capture_id: str = Field(..., description="截取记录ID")
    quality: str = Field(default="medium", description="质量: low/medium/high")
    max_size_mb: float = Field(default=2.0, le=5.0, description="最大大小(MB), 要求<2MB")


# ========== AI成长报告 (日报/周报/月报) (3.3) ==========
class WeeklyReportGenerateRequest(BaseModel):
    """报告生成请求"""
    baby_id: int = Field(..., description="宝宝ID")
    report_type: str = Field(default="weekly", description="报告类型: daily/weekly/monthly")
    period_start: date = Field(..., description="周期开始时间")
    period_end: date = Field(..., description="周期结束时间")


class ReportInfo(BaseModel):
    """报告信息"""
    report_id: int
    baby_id: int
    report_type: str
    period_start: date
    period_end: date
    title: str = Field(..., description="报告标题")
    summary: str = Field(..., description="总结文本")
    sleep_stats: dict | None = None
    cry_stats: dict | None = None
    danger_stats: dict | None = None
    playing_stats: dict | None = None
    milestone_stats: dict | None = None
    recommendations: list[str] = Field(default_factory=list, description="建议")
    status: str = Field(..., description="状态: generating/completed")
    generated_at: datetime | None = None

    model_config = {"from_attributes": True}


class WeeklyReportInfo(BaseModel):
    """周报信息"""
    report_id: str
    baby_id: int
    week_start: datetime
    week_end: datetime
    title: str = Field(..., description="周报标题")
    summary: str = Field(..., description="总结文本")
    highlights: list[dict] = Field(..., description="本周亮点")
    milestones: list[dict] = Field(..., description="里程碑事件")
    sleep_analysis: dict | None = None
    feeding_analysis: dict | None = None
    recommendations: list[str] = Field(..., description="下周建议")
    status: str = Field(..., description="状态: generating/completed")
    generated_at: datetime | None = None

    model_config = {"from_attributes": True}
