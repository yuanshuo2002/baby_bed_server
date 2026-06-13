"""
Schema模块导出
"""
from app.schemas.base import ApiResponse, PageParams, PageResponse
from app.schemas.user import (
    UserRegister, UserLogin, WechatLogin, UserUpdate, UserInfo, TokenResponse,
)
from app.schemas.family import FamilyCreate, FamilyJoin, FamilyUpdate, FamilyInfo, FamilyMemberInfo
from app.schemas.baby import BabyCreate, BabyUpdate, BabyInfo
from app.schemas.device import DeviceRegister, DeviceBind, DeviceModeSwitch, DeviceInfo, DeviceStatus
from app.schemas.event import EventConfirm, EventInfo
from app.schemas.sensor import SensorDataUpload, SensorDataInfo
from app.schemas.voice import (
    VoiceSwitch, ASRRequest, TTSRequest, ChatRequest, VoiceClipInfo, ChatMessageInfo,
)
from app.schemas.routine import RoutineCreate, RoutineUpdate, RoutineInfo, ConflictInfo
from app.schemas.milestone import MilestoneCreate, MilestoneInfo
from app.schemas.report import WeeklyReportGenerate, WeeklyReportInfo

__all__ = [
    "ApiResponse", "PageParams", "PageResponse",
    "UserRegister", "UserLogin", "WechatLogin", "UserUpdate", "UserInfo", "TokenResponse",
    "FamilyCreate", "FamilyJoin", "FamilyUpdate", "FamilyInfo", "FamilyMemberInfo",
    "BabyCreate", "BabyUpdate", "BabyInfo",
    "DeviceRegister", "DeviceBind", "DeviceModeSwitch", "DeviceInfo", "DeviceStatus",
    "EventConfirm", "EventInfo",
    "SensorDataUpload", "SensorDataInfo",
    "VoiceSwitch", "ASRRequest", "TTSRequest", "ChatRequest", "VoiceClipInfo", "ChatMessageInfo",
    "RoutineCreate", "RoutineUpdate", "RoutineInfo", "ConflictInfo",
    "MilestoneCreate", "MilestoneInfo",
    "WeeklyReportGenerate", "WeeklyReportInfo",
]