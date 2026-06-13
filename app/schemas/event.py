"""
监测事件相关Schema
"""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class EventConfirm(BaseModel):
    """事件确认请求"""
    event_id: int = Field(..., description="事件ID")
    parent_handled: int = Field(default=1, description="家长已处理：0-否 1-是")


class EventInfo(BaseModel):
    """事件信息响应"""
    id: int
    baby_id: int
    device_sn: str
    event_type_id: int
    event_level: int | None = None
    trigger_source: str | None = None
    breath_rate: Decimal | None = None
    heart_rate: Decimal | None = None
    sound_db: Decimal | None = None
    body_displace_cm: Decimal | None = None
    pose_angle: Decimal | None = None
    detected_at: datetime | None = None
    resolved_at: datetime | None = None
    duration_sec: int | None = None
    screen_acted: int | None = None
    sound_acted: int | None = None
    app_pushed: int | None = None
    parent_handled: int | None = None
    handled_at: datetime | None = None
    snapshot_url: str | None = None
    video_clip_url: str | None = None
    gif_url: str | None = None
    remark: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
