"""
语音相关Schema
"""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class VoiceSwitch(BaseModel):
    """音色切换请求"""
    clip_id: int = Field(..., description="语音片段ID")


class ASRRequest(BaseModel):
    """语音识别请求"""
    baby_id: int = Field(..., description="宝宝ID")
    audio_data: str = Field(..., description="音频数据(base64)")


class TTSRequest(BaseModel):
    """语音合成请求"""
    baby_id: int = Field(..., description="宝宝ID")
    text: str = Field(..., min_length=1, description="待合成文本")
    voice_role: str | None = Field(None, description="语音角色：mom/dad/nanny/other")


class ChatRequest(BaseModel):
    """对话请求"""
    baby_id: int = Field(..., description="宝宝ID")
    message: str = Field(..., min_length=1, description="用户消息")
    session_id: str | None = Field(None, description="会话ID")


class VoiceClipInfo(BaseModel):
    """语音片段信息响应"""
    id: int
    family_id: int
    voice_role: str
    clip_type: str
    clip_name: str | None = None
    event_type_id: int | None = None
    scenario: str | None = None
    content_text: str | None = None
    audio_url: str
    duration_ms: int | None = None
    file_size_bytes: int | None = None
    tts_model_id: str | None = None
    similarity_score: Decimal | None = None
    is_active: int | None = None
    sort_order: int | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChatMessageInfo(BaseModel):
    """对话消息响应"""
    id: int
    baby_id: int
    session_id: str
    role: str
    content_text: str | None = None
    ltm_tags: str | None = None
    is_ltm_stored: int | None = None
    asr_confidence: Decimal | None = None
    tts_voice_role: str | None = None
    response_latency_ms: int | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class WakeRequest(BaseModel):
    """语音唤醒请求"""
    baby_id: int = Field(..., description="宝宝ID")
    audio_data: str = Field(..., description="音频数据(base64)")
    filter_noise: bool = Field(default=True, description="是否过滤杂音")


class WakeResponse(BaseModel):
    """语音唤醒响应"""
    is_waked: bool = Field(..., description="是否唤醒成功")
    confidence: float = Field(..., ge=0, le=1, description="唤醒置信度")
    wake_word: str | None = Field(None, description="唤醒词")


class IntentRequest(BaseModel):
    """意图识别请求"""
    baby_id: int = Field(..., description="宝宝ID")
    text: str = Field(..., description="用户输入文本")
    context: str | None = Field(None, description="上下文信息")


class IntentResponse(BaseModel):
    """意图识别响应"""
    intent: str = Field(..., description="识别出的意图")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    slots: dict | None = Field(None, description="槽位信息")


class CommandRequest(BaseModel):
    """指令执行请求"""
    baby_id: int = Field(..., description="宝宝ID")
    command: str = Field(..., description="指令类型: light/music/monitor")
    params: dict | None = Field(None, description="指令参数")


class CommandResponse(BaseModel):
    """指令执行响应"""
    command: str
    status: str = Field(..., description="执行状态: success/failed/pending")
    result: str | None = None
    message: str | None = None


class LTMQueryRequest(BaseModel):
    """长记忆查询请求"""
    baby_id: int = Field(..., description="宝宝ID")
    query: str = Field(..., description="查询内容")
    limit: int = Field(default=10, ge=1, le=50, description="返回数量限制")


class LTMStoreRequest(BaseModel):
    """长记忆存储请求"""
    baby_id: int = Field(..., description="宝宝ID")
    content: str = Field(..., description="记忆内容")
    tags: list[str] | None = Field(None, description="标签列表")
    source: str = Field(default="chat", description="来源: chat/event/milestone")


class LTMItem(BaseModel):
    """长记忆项"""
    id: int
    baby_id: int
    content: str
    tags: str | None = None
    source: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class SessionCreateRequest(BaseModel):
    """会话创建请求"""
    baby_id: int = Field(..., description="宝宝ID")
    session_type: str = Field(default="chat", description="会话类型: chat/command")


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    baby_id: int
    session_type: str
    status: str = Field(..., description="状态: active/closed")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ========== 语音克隆系统 (1.1) ==========
class VoiceCloneTrainRequest(BaseModel):
    """语音克隆训练请求"""
    baby_id: int = Field(..., description="宝宝ID")
    voice_role: str = Field(..., description="角色: mom/dad/nanny")
    audio_data: str = Field(..., description="音频数据(base64), 1-3分钟")
    voice_name: str | None = Field(None, description="音色名称")


class VoiceCloneTrainResponse(BaseModel):
    """语音克隆训练响应"""
    voice_id: str
    voice_role: str
    status: str = Field(..., description="训练状态: training/completed/failed")
    similarity_score: float | None = Field(None, ge=0, le=1, description="音色相似度")
    message: str | None = None
    created_at: datetime | None = None


class VoiceInfo(BaseModel):
    """音色信息"""
    voice_id: str
    voice_role: str
    voice_name: str
    is_default: bool
    similarity_score: float | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VoiceSwitchRequest(BaseModel):
    """音色切换请求"""
    voice_id: str = Field(..., description="目标音色ID")
    switch_delay_ms: int = Field(default=0, ge=0, le=1000, description="切换延迟(ms), 要求<200ms")

# ========== 家庭音色库接口 (1.2) ==========
class FamilyVoicePresetCreate(BaseModel):
    voice_role: str = Field(..., description='角色: mom/dad/nanny/other')
    voice_name: str | None = Field(None, description='音色名称')
    audio_data: str | None = Field(None, description='音频数据(base64)，用于调用克隆API')
    audio_url: str | None = Field(None, description='音频URL')
    duration_ms: int | None = Field(None, description='音频时长(ms)')
    similarity_score: float | None = Field(None, ge=0, le=1, description='相似度评分')
    is_default: bool = Field(default=False, description='是否设为默认音色')


class FamilyVoicePresetUpdate(BaseModel):
    voice_name: str | None = Field(None, description='音色名称')
    audio_url: str | None = Field(None, description='音频URL')
    duration_ms: int | None = Field(None, description='音频时长(ms)')
    similarity_score: float | None = Field(None, ge=0, le=1, description='相似度评分')
    is_default: bool | None = Field(None, description='是否设为默认音色')


class FamilyVoicePresetInfo(BaseModel):
    id: int
    family_id: int
    voice_id: str
    voice_role: str
    voice_name: str | None = None
    audio_url: str | None = None
    duration_ms: int | None = None
    similarity_score: float | None = None
    is_default: bool
    is_active: int | None = None
    sort_order: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
