"""
K230 视频识别服务
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.schemas.video import VideoCreate, VideoUpdate


class VideoService:
    """K230 视频识别结果服务"""

    @staticmethod
    async def create(db: AsyncSession, video_data: VideoCreate) -> Video:
        """创建视频记录"""
        video = Video(**video_data.model_dump())
        db.add(video)
        await db.flush()
        await db.refresh(video)
        return video

    @staticmethod
    async def get_by_id(db: AsyncSession, video_id: int) -> Video | None:
        """根据ID获取视频记录"""
        result = await db.execute(select(Video).where(Video.id == video_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_device(db: AsyncSession, device_sn: str) -> list[Video]:
        """根据设备序列号获取视频列表"""
        result = await db.execute(
            select(Video)
            .where(Video.device_sn == device_sn)
            .order_by(Video.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_paginated(
        db: AsyncSession, device_sn: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Video], int]:
        """分页获取视频列表"""
        # 计算总数
        count_result = await db.execute(
            select(func.count()).select_from(Video).where(Video.device_sn == device_sn)
        )
        total = count_result.scalar() or 0

        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询数据
        result = await db.execute(
            select(Video)
            .where(Video.device_sn == device_sn)
            .order_by(Video.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def update(db: AsyncSession, video_id: int, video_data: VideoUpdate) -> Video | None:
        """更新视频记录"""
        video = await VideoService.get_by_id(db, video_id)
        if not video:
            return None

        update_data = video_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(video, key, value)

        await db.flush()
        await db.refresh(video)
        return video

    @staticmethod
    async def delete(db: AsyncSession, video_id: int) -> bool:
        """删除视频记录"""
        video = await VideoService.get_by_id(db, video_id)
        if not video:
            return False

        await db.delete(video)
        await db.flush()
        return True


video_service = VideoService()
