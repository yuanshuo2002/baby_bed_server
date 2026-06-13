"""
系统管理Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any


class DataSyncRequest(BaseModel):
    """数据同步请求"""
    device_sn: str = Field(..., description="设备序列号")
    sync_type: str = Field(..., description="同步类型: full/incremental")
    sync_direction: str = Field(..., description="同步方向: upload/download")


class PerformanceUpload(BaseModel):
    """性能数据上报请求"""
    device_sn: str = Field(..., description="设备序列号")
    timestamp: datetime | None = Field(None, description="上报时间")
    cpu_percent: float | None = Field(None, ge=0, le=100, description="CPU使用率(%)")
    memory_used_mb: int | None = Field(None, ge=0, description="已用内存(MB)")
    memory_total_mb: int | None = Field(None, ge=0, description="总内存(MB)")
    disk_used_mb: int | None = Field(None, ge=0, description="已用存储(MB)")
    disk_total_mb: int | None = Field(None, ge=0, description="总存储(MB)")
    uptime_seconds: int | None = Field(None, ge=0, description="运行时间(秒)")
    network_latency_ms: float | None = Field(None, ge=0, description="网络延迟(ms)")
    temperature_celsius: float | None = Field(None, description="设备温度(℃)")


class PerformanceUploadResponse(BaseModel):
    """性能数据上报响应"""
    device_sn: str
    status: str = Field(..., description="处理状态: accepted/rejected")
    record_id: int | None = Field(None, description="记录ID")
    message: str | None = None


class HealthUpload(BaseModel):
    """健康状态上报请求"""
    device_sn: str = Field(..., description="设备序列号")
    timestamp: datetime | None = Field(None, description="上报时间")
    health_status: str = Field(default="ok", description="健康状态: ok/warning/critical")
    emc_certified: bool | None = Field(None, description="EMC认证状态")
    safety_certified: bool | None = Field(None, description="安全认证状态")
    error_codes: list[str] = Field(default=[], description="错误码列表")
    warning_messages: list[str] = Field(default=[], description="警告信息列表")
    hardware_version: str | None = Field(None, description="硬件版本")
    firmware_version: str | None = Field(None, description="固件版本")


class HealthUploadResponse(BaseModel):
    """健康状态上报响应"""
    device_sn: str
    status: str = Field(..., description="处理状态: accepted/rejected")
    record_id: int | None = Field(None, description="记录ID")
    message: str | None = None


class SyncUploadData(BaseModel):
    """同步数据项"""
    data_type: str = Field(..., description="数据类型: sensor/event/status_log")
    data: list[dict[str, Any]] = Field(..., description="数据内容")


class SyncUploadRequest(BaseModel):
    """数据同步上传请求"""
    device_sn: str = Field(..., description="设备序列号")
    sync_id: str | None = Field(None, description="同步批次ID")
    sync_type: str = Field(default="incremental", description="同步类型: full/incremental")
    records: list[SyncUploadData] = Field(default=[], description="同步数据")


class SyncUploadResponse(BaseModel):
    """数据同步上传响应"""
    device_sn: str
    sync_id: str
    status: str = Field(..., description="处理状态: completed/partial/failed")
    records_processed: int = Field(..., description="已处理记录数")
    records_failed: int = Field(..., description="失败记录数")
    errors: list[dict] = Field(default=[], description="错误详情")