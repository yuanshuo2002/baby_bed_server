"""
硬件端视频上传和管理相关接口
"""
import os
import shutil
import subprocess
import uuid
from pathlib import Path as PathLike

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.response import success
from config import settings
from app.schemas.base import ApiResponse
from app.schemas.video import VideoCreate, VideoResponse, VideoUpdate
from app.services.video_service import video_service

router = APIRouter(prefix="/video", tags=["视频识别"])

# 视频存储目录
VIDEO_UPLOAD_DIR = PathLike("uploads/videos")
VIDEO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_COVER_DIR = VIDEO_UPLOAD_DIR / "covers"
VIDEO_COVER_DIR.mkdir(parents=True, exist_ok=True)

# 允许的视频格式
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/mpeg", "video/quicktime", "video/x-msvideo"}


def _get_video_url(filename: str) -> str:
    """生成视频访问URL"""
    return f"/api/v1/video/stream/{filename}"


def _get_image_url(filename: str) -> str:
    """生成封面图片访问URL"""
    return f"/api/v1/video/image/{filename}"


def _save_first_frame(video_path: PathLike, image_path: PathLike) -> None:
    """使用 ffmpeg 截取视频第一帧作为封面"""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("服务器未安装 ffmpeg，无法生成视频封面")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(image_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@router.post("/upload", response_model=ApiResponse, summary="上传视频文件 [硬件接口]")
async def upload_video(
    device_sn: str = Query(..., description="设备序列号"),
    video_content_text: str | None = Query(None, description="视频AI理解后的文字内容"),
    file: UploadFile = File(..., description="视频文件"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    上传视频文件（硬件端调用）
    - 保存文件到本地
    - 返回视频访问URL
    """
    # 校验文件类型
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        return success(data=None, message=f"不支持的视频格式: {file.content_type}")

    # 生成唯一文件名
    ext = PathLike(file.filename or "video.mp4").suffix or ".mp4"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = VIDEO_UPLOAD_DIR / filename
    cover_filename = f"{PathLike(filename).stem}.jpg"
    cover_filepath = VIDEO_COVER_DIR / cover_filename

    # 保存文件
    try:
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        _save_first_frame(filepath, cover_filepath)
    except Exception as e:
        if filepath.exists():
            filepath.unlink(missing_ok=True)
        if cover_filepath.exists():
            cover_filepath.unlink(missing_ok=True)
        return success(data=None, message=f"文件保存失败: {str(e)}")

    # 生成访问URL
    video_url = _get_video_url(filename)
    img_url = _get_image_url(cover_filename)

    # 保存到数据库
    video_data = VideoCreate(
        device_sn=device_sn,
        video_url=video_url,
        img_url=img_url,
        video_content_text=video_content_text,
    )
    video = await video_service.create(db, video_data)

    return success(
        data={
            "id": video.id,
            "video_url": video_url,
            "img_url": img_url,
            "filename": filename,
        },
        message="视频上传成功"
    )


@router.get("/stream/{filename}", summary="获取视频流")
async def stream_video(
    filename: str = Path(..., description="视频文件名"),
):
    """
    视频流接口
    支持直接播放或下载视频
    """
    filepath = VIDEO_UPLOAD_DIR / filename

    if not filepath.exists():
        return {"error": "视频文件不存在"}

    # 推断内容类型
    ext = PathLike(filename).suffix.lower()
    content_types = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mpeg": "video/mpeg",
        ".mov": "video/quicktime",
    }
    content_type = content_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=filepath,
        media_type=content_type,
        filename=filename,
        headers={"Accept-Ranges": "bytes"}
    )


@router.get("/image/{filename}", summary="获取视频封面图")
async def stream_video_image(
    filename: str = Path(..., description="封面图片文件名"),
):
    """
    视频封面图接口
    """
    filepath = VIDEO_COVER_DIR / filename

    if not filepath.exists():
        return {"error": "图片文件不存在"}

    return FileResponse(
        path=filepath,
        media_type="image/jpeg",
        filename=filename,
    )


@router.get("/get/{video_id}", response_model=ApiResponse, summary="视频信息根据id查询 [硬件接口]")
async def get_video(
    video_id: int = Path(..., description="视频ID"),
    db: AsyncSession = Depends(get_db_session),
):
    """根据ID查询视频信息"""
    video = await video_service.get_by_id(db, video_id)
    if not video:
        return success(data=None, message="视频不存在")

    return success(data=VideoResponse.model_validate(video))


@router.put("/update/{video_id}", response_model=ApiResponse, summary="更新视频信息 [硬件接口]")
async def update_video(
    video_id: int = Path(..., description="视频ID"),
    video_data: VideoUpdate = ...,
    db: AsyncSession = Depends(get_db_session),
):
    """根据ID更新视频信息"""
    video = await video_service.update(db, video_id, video_data)
    if not video:
        return success(data=None, message="视频不存在")

    return success(message="视频信息更新成功")


@router.delete("/delete/{video_id}", response_model=ApiResponse, summary="删除视频信息 [硬件接口]")
async def delete_video(
    video_id: int = Path(..., description="视频ID"),
    db: AsyncSession = Depends(get_db_session),
):
    """根据ID删除视频信息"""
    success_flag = await video_service.delete(db, video_id)
    if not success_flag:
        return success(data=None, message="视频不存在")

    return success(message="视频信息删除成功")


@router.get("/by-device/{device_sn}", response_model=ApiResponse, summary="根据设备序列号查询 [硬件接口]")
async def get_videos_by_device(
    device_sn: str = Path(..., description="设备序列号"),
    db: AsyncSession = Depends(get_db_session),
):
    """根据设备序列号查询所有视频"""
    videos = await video_service.get_by_device(db, device_sn)
    return success(data=[VideoResponse.model_validate(v) for v in videos])


@router.get("/list", response_model=ApiResponse, summary="分页查询视频列表 [硬件接口]")
async def get_video_list(
    device_sn: str = Query(..., description="设备序列号"),
    page_index: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db_session),
):
    """分页查询视频列表"""
    items, total = await video_service.get_paginated(db, device_sn, page_index, page_size)

    return success(
        data={
            "list": [VideoResponse.model_validate(v) for v in items],
            "total": total,
        }
    )
