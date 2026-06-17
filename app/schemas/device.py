"""
设备相关Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class DeviceRegister(BaseModel):
    """设备注册请求"""
    device_sn: str = Field(..., min_length=1, max_length=64, description="设备序列号")
    device_name: str = Field(..., min_length=1, max_length=100, description="设备名称")
    device_model: str | None = Field(None, max_length=50, description="设备型号")


class DeviceBind(BaseModel):
    """设备绑定请求（baby_id可选）"""
    device_sn: str = Field(..., description="设备序列号")
    baby_id: int | None = Field(None, description="绑定的宝宝ID（可选，后续可在宝宝管理中添加）")


class DeviceBindBaby(BaseModel):
    """设备绑定宝宝请求"""
    device_sn: str = Field(..., description="设备序列号")
    baby_id: int = Field(..., description="绑定的宝宝ID")


class DeviceModeSwitch(BaseModel):
    """设备模式切换请求"""
    device_sn: str = Field(..., description="设备序列号")
    target_mode: str = Field(..., description="目标模式：sleep/play/co_sleep")
    switch_type: str = Field(default="manual", description="切换类型：manual/auto")
    switch_reason: str | None = Field(None, description="切换原因")


class DeviceInfo(BaseModel):
    """设备信息响应"""
    id: int
    device_sn: str
    baby_id: int | None = None
    device_name: str | None = None
    device_model: str | None = None
    firmware_version: str | None = None
    work_mode: str | None = None
    online_status: int | None = None
    last_online_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DeviceStatus(BaseModel):
    """设备状态响应"""
    device_sn: str
    online_status: int | None = None
    work_mode: str | None = None
    last_online_at: datetime | None = None


class ThemeConfig(BaseModel):
    """主题配置请求"""
    theme_name: str = Field(default="warm", description="主题名称: warm/fresh/calm")
    primary_color: str | None = Field(None, description="主色调")
    font_size: str = Field(default="medium", description="字体大小: small/medium/large")
    animation_enabled: bool = Field(default=True, description="是否启用动画")


class ThemeConfigResponse(BaseModel):
    """主题配置响应"""
    user_id: int
    theme_name: str
    primary_color: str | None = None
    font_size: str
    animation_enabled: bool
    updated_at: datetime | None = None



class UpdateDeviceName(BaseModel):
    """更新设备名称请求"""
    device_sn: str = Field(..., description="设备序列号")
    device_name: str = Field(..., min_length=1, max_length=100, description="新的设备名称")


class HeartbeatRequest(BaseModel):
    """设备心跳请求"""
    device_sn: str = Field(..., description="设备序列号")
    work_mode: str | None = Field(None, description="当前工作模式")
    online_status: int | None = Field(1, description="在线状态: 1=在线, 0=离线")
    cpu_percent: float | None = Field(None, ge=0, le=100, description="CPU使用率(%)")
    memory_percent: float | None = Field(None, ge=0, le=100, description="内存使用率(%)")


class HeartbeatResponse(BaseModel):
    """设备心跳响应"""
    device_sn: str
    is_bound: bool = Field(..., description="是否已绑定")
    baby_id: int | None = Field(None, description="绑定的宝宝ID，未绑定时为null")
    family_id: int | None = Field(None, description="家庭ID")
    work_mode: str | None = Field(None, description="当前工作模式")
    online_status: int = Field(..., description="在线状态: 1=在线, 0=离线")
    last_bind_at: str | None = Field(None, description="最后绑定时间")