"""
长记忆(LTM)服务 - 调用远程管理服务接口
视觉/语音/雷达事件统一时间轴存储
"""
from typing import Any
import httpx
import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import settings


class LTMService:
    """长记忆服务"""

    BASE_URL = settings.LTM_API_URL
    TIMEOUT = 60.0

    @classmethod
    async def upload_event(cls, description: str, profile_id: int = 1) -> dict[str, Any]:
        """上传MLLM描述文本，自动识别事件类型/情绪/姿态"""
        async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
            resp = await client.post(
                f"{cls.BASE_URL}/events",
                json={"body_text": description},
            )
            resp.raise_for_status()
            return resp.json()

    @classmethod
    async def get_timeline(
        cls,
        profile_id: int = 1,
        date: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict[str, Any]:
        """获取统一时间轴事件列表"""
        params: dict[str, Any] = {"profile_id": profile_id, "page": page, "limit": limit}
        if date:
            params["date"] = date
        if event_type:
            params["type"] = event_type

        async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
            resp = await client.get(f"{cls.BASE_URL}/events", params=params)
            resp.raise_for_status()
            return resp.json()

    @classmethod
    async def get_event_detail(cls, event_id: str) -> dict[str, Any]:
        """获取事件详情"""
        async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
            resp = await client.get(f"{cls.BASE_URL}/events/{event_id}")
            resp.raise_for_status()
            return resp.json()

    @classmethod
    async def get_memory(cls) -> dict[str, Any]:
        """获取三层记忆库 L0/L1/L2"""
        async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
            resp = await client.get(f"{cls.BASE_URL}/memory")
            resp.raise_for_status()
            return resp.json()

    @classmethod
    async def get_daily_summary(cls, summary_type: str = "day") -> dict[str, Any]:
        """获取每日/每小时摘要"""
        async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
            resp = await client.get(f"{cls.BASE_URL}/summaries/{summary_type}")
            resp.raise_for_status()
            return resp.json()

    @classmethod
    async def batch_extract(cls, descriptions: list[str], profile_id: int = 1) -> dict[str, Any]:
        """批量上传MLLM描述文本"""
        async with httpx.AsyncClient(timeout=cls.TIMEOUT * 2) as client:
            resp = await client.post(
                f"{cls.BASE_URL}/pipeline/extract",
                json={"descriptions": descriptions, "profile_id": profile_id},
            )
            resp.raise_for_status()
            return resp.json()

    @classmethod
    async def ask(cls, question: str, profile_id: int = 1) -> dict[str, Any]:
        """自然语言问答查询事件"""
        async with httpx.AsyncClient(timeout=cls.TIMEOUT * 2) as client:
            resp = await client.post(
                f"{cls.BASE_URL}/ask",
                json={"question": question, "profile_id": profile_id},
            )
            resp.raise_for_status()
            return resp.json()

    @classmethod
    async def delete_event(cls, event_id: str) -> dict[str, Any]:
        """删除事件"""
        async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
            resp = await client.post(
                f"{cls.BASE_URL}/events/delete",
                json={"event_id": event_id},
            )
            resp.raise_for_status()
            return resp.json()

    @classmethod
    async def rebuild_memory(cls) -> dict[str, Any]:
        """重建记忆库"""
        async with httpx.AsyncClient(timeout=cls.TIMEOUT * 3) as client:
            resp = await client.post(f"{cls.BASE_URL}/pipeline/build")
            resp.raise_for_status()
            return resp.json()


ltm_service = LTMService()