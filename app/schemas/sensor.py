"""
传感器数据相关Schema
"""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class SensorDataUpload(BaseModel):
    """传感器数据上传请求"""
    device_sn: str = Field(..., description="设备序列号")
    baby_id: int | None = Field(None, description="宝宝ID（可选，未传时自动通过device_sn查询）")
    collected_at: datetime = Field(..., description="采集时间")
    breath_rate: Decimal | None = Field(None, description="呼吸频率")
    heart_rate: Decimal | None = Field(None, description="心率")
    body_movement: Decimal | None = Field(None, description="体动活跃度")
    distance_cm: Decimal | None = Field(None, description="雷达测距")
    sound_db: Decimal | None = Field(None, description="环境分贝")
    sound_type: str | None = Field(None, description="声音分类")
    pose_status: str | None = Field(None, description="姿态状态")
    face_detected: int | None = Field(None, description="是否检测到面部")
    expression: str | None = Field(None, description="表情分类")
    body_offset_cm: Decimal | None = Field(None, description="身体距床边距离")
    roll_angle: Decimal | None = Field(None, description="翻转角度")
    height_cm: Decimal | None = Field(None, description="头部高度")
    room_temp: Decimal | None = Field(None, description="室温")
    humidity: Decimal | None = Field(None, description="湿度")
    noise_db: Decimal | None = Field(None, description="环境噪声")


class SensorDataInfo(BaseModel):
    """传感器数据响应"""
    id: int
    device_sn: str
    baby_id: int
    collected_at: datetime | None = None
    breath_rate: Decimal | None = None
    heart_rate: Decimal | None = None
    body_movement: Decimal | None = None
    distance_cm: Decimal | None = None
    sound_db: Decimal | None = None
    sound_type: str | None = None
    pose_status: str | None = None
    face_detected: int | None = None
    expression: str | None = None
    body_offset_cm: Decimal | None = None
    roll_angle: Decimal | None = None
    height_cm: Decimal | None = None
    room_temp: Decimal | None = None
    humidity: Decimal | None = None
    noise_db: Decimal | None = None

    model_config = {"from_attributes": True}


# ========== 多模态融合监测 (2.1) ==========
class SensorFusionRequest(BaseModel):
    """多模态融合分析请求"""
    device_sn: str = Field(..., description="设备序列号")
    baby_id: int = Field(..., description="宝宝ID")
    video_data: str | None = Field(None, description="视频帧数据(base64)")
    radar_data: dict | None = Field(None, description="雷达数据")
    audio_data: str | None = Field(None, description="音频数据(base64)")


class SensorFusionResponse(BaseModel):
    """多模态融合分析响应"""
    device_sn: str
    baby_id: int
    fused_status: str = Field(..., description="融合判定状态: sleeping/awake/playing/crying/danger")
    confidence: float = Field(..., ge=0, le=1, description="综合置信度, 要求>0.90")
    details: dict = Field(..., description="各模态分析详情")
    alert_level: str | None = Field(None, description="告警级别: none/low/medium/high")
    timestamp: datetime | None = None


# ========== 五类场景分级响应 (2.2) ==========
class SceneClassifyResponse(BaseModel):
    """场景分类响应"""
    baby_id: int
    scene_type: str = Field(..., description="场景类型: sleeping/awake/playing/crying/danger")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    triggers: list[str] = Field(default=[], description="触发条件列表")
    timestamp: datetime | None = None


class SceneResponseRequest(BaseModel):
    """场景响应执行请求"""
    baby_id: int = Field(..., description="宝宝ID")
    scene_type: str = Field(..., description="场景类型")
    response_mode: str = Field(default="auto", description="响应模式: auto/manual")


class SceneResponseScript(BaseModel):
    """场景响应脚本"""
    script_id: str
    scene_type: str
    actions: list[dict] = Field(..., description="执行动作列表")
    light_config: dict | None = None
    sound_config: dict | None = None
    screen_animation: str | None = None
    push_notification: bool = True
    message: str | None = None
