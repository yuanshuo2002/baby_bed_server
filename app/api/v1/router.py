"""
API v1 总路由注册
将所有子路由注册到 /api/v1 前缀下
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.family import router as family_router
from app.api.v1.baby import router as baby_router
from app.api.v1.voice import router as voice_router
from app.api.v1.sensor import router as sensor_router
from app.api.v1.response import router as response_router
from app.api.v1.routine import router as routine_router
from app.api.v1.milestone import router as milestone_router
from app.api.v1.device import router as device_router
from app.api.v1.hardware import router as hardware_router
from app.api.v1.user import router as user_router
from app.api.v1.moment import router as moment_router
from app.api.v1.learning import router as learning_router
from app.api.v1.status import router as status_router
from app.api.v1.video import router as video_router
from app.api.v1.interaction import router as interaction_router
from app.api.v1.system import router as system_router
from app.api.v1.push import router as push_router

api_router = APIRouter()

# 注册健康检查端点
@api_router.get("/health", summary="健康检查")
async def health_check():
    """API健康检查端点，用于监控服务运行状态"""
    return {"status": "ok", "message": "Baby Bed Server is running"}

# 注册各模块子路由
api_router.include_router(auth_router)
api_router.include_router(family_router)
api_router.include_router(baby_router)
api_router.include_router(voice_router)
api_router.include_router(sensor_router)
api_router.include_router(response_router)
api_router.include_router(routine_router)
api_router.include_router(milestone_router)
api_router.include_router(device_router)
api_router.include_router(hardware_router)
api_router.include_router(user_router)
api_router.include_router(moment_router)
api_router.include_router(learning_router)
api_router.include_router(status_router)
api_router.include_router(video_router)
api_router.include_router(interaction_router)
api_router.include_router(system_router)
api_router.include_router(push_router)