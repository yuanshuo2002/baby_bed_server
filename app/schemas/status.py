"""
状态日志相关Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ========== 状态日志 ==========
class StatusLogCreate(BaseModel):
    """状态日志创建请求"""
    baby_id: int = Field(..., description="宝宝ID")
    device_sn: str = Field(..., description="设备序列号")
    status_type: str = Field(..., description="状态类型: sleeping/awake/playing/crying/danger")
    status_level: int = Field(default=0, ge=0, le=3, description="状态级别(哭闹1-3级)")
    started_at: datetime = Field(..., description="状态开始时间")
    breath_rate: Decimal | None = Field(None, description="呼吸频率")
    heart_rate: Decimal | None = Field(None, description="心率")
    sound_db: Decimal | None = Field(None, description="声音分贝")
    pose_status: str | None = Field(None, description="姿态")
    expression: str | None = Field(None, description="表情")


class StatusLogInfo(BaseModel):
    """状态日志信息"""
    id: int
    baby_id: int
    device_sn: str
    status_type: str
    status_level: int
    started_at: datetime
    ended_at: datetime | None = None
    duration_sec: int | None = None
    breath_rate: Decimal | None = None
    heart_rate: Decimal | None = None
    sound_db: Decimal | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ========== 哭闹事件 ==========
class CryEventCreate(BaseModel):
    """哭闹事件创建请求"""
    baby_id: int = Field(..., description="宝宝ID")
    device_sn: str = Field(..., description="设备序列号")
    cry_level: int = Field(..., ge=1, le=3, description="哭闹级别: 1=轻微, 2=有节奏, 3=剧烈")
    cry_type: str | None = Field(None, description="哭闹类型: hunger/discomfort/pain/attention/unknown")
    started_at: datetime = Field(..., description="开始时间")
    sound_db: Decimal | None = Field(None, description="声音分贝")
    heart_rate: Decimal | None = Field(None, description="心率")
    body_movement: Decimal | None = Field(None, description="体动活跃度")
    expression: str | None = Field(None, description="表情")


class CryEventHandle(BaseModel):
    """哭闹事件处理请求"""
    handle_method: str = Field(..., description="处理方式: feeding/holding/comfort/other")


class CryEventInfo(BaseModel):
    """哭闹事件信息"""
    id: int
    baby_id: int
    cry_level: int
    cry_type: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_sec: int | None = None
    sound_db: Decimal | None = None
    lullaby_played: int = 0
    parent_handled: int = 0
    snapshot_url: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ========== 危险事件 ==========
class DangerEventCreate(BaseModel):
    """危险事件创建请求"""
    baby_id: int = Field(..., description="宝宝ID")
    device_sn: str = Field(..., description="设备序列号")
    danger_type: str = Field(..., description="危险类型: breath_pause/near_edge/climbing/body_out/standing/prone_sleep/face_covered")
    severity: int = Field(..., ge=1, le=3, description="严重程度: 1=警告, 2=危险, 3=紧急")
    detected_at: datetime = Field(..., description="检测时间")
    breath_rate: Decimal | None = Field(None, description="呼吸频率")
    heart_rate: Decimal | None = Field(None, description="心率")
    body_offset_cm: Decimal | None = Field(None, description="身体偏移距离")
    pose_status: str | None = Field(None, description="姿态")


class DangerEventHandle(BaseModel):
    """危险事件处理请求"""
    handle_result: str = Field(..., description="处理结果: resolved/false_alarm/ongoing")


class DangerEventInfo(BaseModel):
    """危险事件信息"""
    id: int
    baby_id: int
    danger_type: str
    severity: int
    detected_at: datetime
    ended_at: datetime | None = None
    duration_sec: int | None = None
    alert_played: int = 0
    push_sent: int = 0
    parent_handled: int = 0
    snapshot_url: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ========== 睡眠报告 ==========
class SleepReportInfo(BaseModel):
    """睡眠报告信息"""
    id: int
    baby_id: int
    report_date: datetime
    total_sleep_min: int
    night_sleep_min: int
    day_sleep_min: int
    nap_count: int
    longest_sleep_min: int
    sleep_score: int | None = None
    cry_count: int = 0
    danger_count: int = 0
    ai_summary: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
