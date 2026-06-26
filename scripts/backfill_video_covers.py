"""
回填历史视频记录的封面图与 img_url

用法:
    uv run python scripts/backfill_video_covers.py
"""
from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.video import Video


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VIDEO_ROOT = PROJECT_ROOT / "uploads" / "videos"
COVER_ROOT = VIDEO_ROOT / "covers"


def _video_filename_from_url(video_url: str) -> str:
    """从 /api/v1/video/stream/<filename> 中提取文件名"""
    path = urlsplit(video_url).path
    return Path(path).name


def _cover_url(filename: str) -> str:
    return f"/api/v1/video/image/{filename}"


def _ensure_cover(video_path: Path, cover_path: Path) -> None:
    """用 ffmpeg 从视频第一帧生成封面图"""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("服务器未安装 ffmpeg，无法生成视频封面")

    cover_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg_bin,
            "-y",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(cover_path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video).where((Video.img_url.is_(None)) | (Video.img_url == ""))
        )
        videos = list(result.scalars().all())

        if not videos:
            print("没有需要回填的记录")
            return

        print(f"发现 {len(videos)} 条需要回填的记录")

        updated = 0
        skipped = 0

        for video in videos:
            try:
                filename = _video_filename_from_url(video.video_url)
                video_path = VIDEO_ROOT / filename
                if not video_path.exists():
                    print(f"[跳过] 视频文件不存在: {video_path}")
                    skipped += 1
                    continue

                cover_filename = f"{Path(filename).stem}.jpg"
                cover_path = COVER_ROOT / cover_filename
                _ensure_cover(video_path, cover_path)

                video.img_url = _cover_url(cover_filename)
                await db.flush()
                updated += 1
                print(f"[成功] {video.id} -> {video.img_url}")
            except Exception as exc:  # noqa: BLE001
                skipped += 1
                print(f"[失败] {video.id}: {exc}")

        await db.commit()
        print(f"回填完成，成功 {updated} 条，跳过 {skipped} 条")


if __name__ == "__main__":
    asyncio.run(main())
