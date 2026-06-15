"""
Baby Bed Server - FastAPI应用入口
智能婴儿床后端服务
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.exceptions import BusinessException
from app.api.v1.router import api_router
from app.services.device_service import DeviceService
from app.services.sensor_service import SensorService
from app.database import AsyncSessionLocal
from config import settings


async def cleanup_offline_devices_task():
    """后台定时任务：清理离线设备"""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                result = await DeviceService.cleanup_offline_devices(db, timeout_minutes=5)
                if result["cleaned_count"] > 0:
                    print(f"[定时任务] 清理了 {result['cleaned_count']} 个离线设备: {result['device_sns']}")
        except Exception as e:
            print(f"[定时任务] 清理离线设备失败: {e}")
        await asyncio.sleep(60)  # 每60秒执行一次


async def cleanup_sensor_data_task():
    """后台定时任务：清理过期的传感器原始数据
    硬件端每几秒上传一条数据，数据量增长很快
    默认保留最近7天数据，每小时执行一次
    """
    while True:
        try:
            async with AsyncSessionLocal() as db:
                result = await SensorService.cleanup_old_sensor_data(db, retention_days=15)
                if result["deleted_count"] > 0:
                    print(f"[定时任务] 清理了 {result['deleted_count']} 条过期传感器数据 (保留{result['retention_days']}天)")
        except Exception as e:
            print(f"[定时任务] 清理传感器数据失败: {e}")
        await asyncio.sleep(3600)  # 每小时执行一次


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化资源，关闭时释放资源
    """
    # 启动时执行
    print(f"[启动] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[启动] 数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    # 启动后台定时任务
    cleanup_device_task = asyncio.create_task(cleanup_offline_devices_task())
    cleanup_sensor_task = asyncio.create_task(cleanup_sensor_data_task())
    print("[启动] 离线设备清理任务已启动")
    print("[启动] 传感器数据清理任务已启动（每小时执行）")

    yield

    # 关闭时执行
    cleanup_device_task.cancel()
    cleanup_sensor_task.cancel()
    try:
        await cleanup_device_task
        await cleanup_sensor_task
    except asyncio.CancelledError:
        pass
    print("[关闭] 应用正在关闭...")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.message, "data": None},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器 - 捕获所有未处理的异常"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": f"服务器内部错误: {str(exc)}", "data": None},
    )


# 注册 API 路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)