"""
语音交互业务逻辑层
"""
import uuid
import httpx
from datetime import datetime
from sqlalchemy import select, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ExternalApiException
from app.models.voice_clip import ParentVoiceClip
from app.models.family_voice_preset import FamilyVoicePreset
from app.models.conversation import ConversationContext
from app.services.family_service import FamilyService


class VoiceService:
    """语音交互服务"""

    @staticmethod
    async def clone_voice(db: AsyncSession, user_id: int, baby_id: int, clip_name: str, audio_url: str) -> dict:
        """上传语音克隆（保存记录）"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        clip = ParentVoiceClip(
            family_id=family.id,
            voice_role="mom",
            clip_type="clone_sample",
            clip_name=clip_name,
            audio_url=audio_url,
        )
        db.add(clip)
        await db.flush()
        return {"id": clip.id, "message": "语音克隆任务已提交"}

    @staticmethod
    async def get_voice_clips(db: AsyncSession, user_id: int, baby_id: int) -> list[dict]:
        """获取语音片段列表"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        query = select(ParentVoiceClip).where(
            ParentVoiceClip.family_id == family.id,
            ParentVoiceClip.is_active == 1,
        ).order_by(ParentVoiceClip.sort_order)

        result = await db.execute(query)
        clips = result.scalars().all()
        return [
            {
                "id": c.id,
                "family_id": c.family_id,
                "voice_role": c.voice_role,
                "clip_type": c.clip_type,
                "clip_name": c.clip_name,
                "event_type_id": c.event_type_id,
                "scenario": c.scenario,
                "content_text": c.content_text,
                "audio_url": c.audio_url,
                "duration_ms": c.duration_ms,
                "file_size_bytes": c.file_size_bytes,
                "tts_model_id": c.tts_model_id,
                "similarity_score": float(c.similarity_score) if c.similarity_score else None,
                "is_active": c.is_active,
            }
            for c in clips
        ]

    @staticmethod
    async def delete_voice_clip(db: AsyncSession, user_id: int, clip_id: int) -> None:
        """删除语音片段"""
        result = await db.execute(select(ParentVoiceClip).where(ParentVoiceClip.id == clip_id))
        clip = result.scalar_one_or_none()
        if not clip:
            raise NotFoundException("语音片段不存在")
        clip.is_active = 0
        await db.flush()

    @staticmethod
    async def chat(db: AsyncSession, user_id: int, baby_id: int, message: str, session_id: str | None = None) -> dict:
        """LLM对话"""
        if not session_id:
            session_id = uuid.uuid4().hex[:16]

        # 保存用户消息
        user_msg = ConversationContext(
            baby_id=baby_id,
            session_id=session_id,
            role="user",
            content_text=message,
        )
        db.add(user_msg)
        await db.flush()

        # TODO: 调用LLM API获取回复
        reply_text = f"（AI回复占位）收到消息：{message[:20]}..."

        # 保存AI回复
        assistant_msg = ConversationContext(
            baby_id=baby_id,
            session_id=session_id,
            role="assistant",
            content_text=reply_text,
        )
        db.add(assistant_msg)
        await db.flush()

        return {"reply": reply_text, "session_id": session_id}

    @staticmethod
    async def get_chat_history(db: AsyncSession, user_id: int, baby_id: int, session_id: str | None = None) -> list[dict]:
        """获取对话历史"""
        query = select(ConversationContext).where(ConversationContext.baby_id == baby_id)
        if session_id:
            query = query.where(ConversationContext.session_id == session_id)
        query = query.order_by(ConversationContext.created_at).limit(100)

        result = await db.execute(query)
        messages = result.scalars().all()
        return [
            {
                "id": m.id,
                "baby_id": m.baby_id,
                "session_id": m.session_id,
                "role": m.role,
                "content_text": m.content_text,
                "ltm_tags": m.ltm_tags,
                "is_ltm_stored": m.is_ltm_stored,
                "asr_confidence": float(m.asr_confidence) if m.asr_confidence else None,
                "tts_voice_role": m.tts_voice_role,
                "response_latency_ms": m.response_latency_ms,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]

    @staticmethod
    async def create_session(db: AsyncSession, user_id: int, baby_id: int, session_type: str = "chat") -> dict:
        """创建会话"""
        session_id = uuid.uuid4().hex[:16]
        return {
            "session_id": session_id,
            "baby_id": baby_id,
            "session_type": session_type,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    @staticmethod
    async def close_session(db: AsyncSession, user_id: int, session_id: str) -> dict:
        """关闭会话"""
        return {
            "session_id": session_id,
            "status": "closed",
            "message": "会话已关闭",
        }

    @staticmethod
    async def switch_voice(db: AsyncSession, user_id: int, voice_id: str) -> dict:
        """切换默认音色"""
        family = await FamilyService._get_user_family_obj(db, user_id)

        # 查找目标音色
        result = await db.execute(
            select(FamilyVoicePreset).where(
                FamilyVoicePreset.voice_id == voice_id,
                FamilyVoicePreset.family_id == family.id,
                FamilyVoicePreset.is_active == 1,
            )
        )
        preset = result.scalar_one_or_none()
        if not preset:
            raise NotFoundException('音色记录不存在')

        # 先取消所有默认音色
        await db.execute(
            text("UPDATE family_voice_presets SET is_default=0 WHERE family_id=:family_id AND is_default=1")
            .bindparams(family_id=family.id)
        )

        # 设置新默认音色
        preset.is_default = 1
        await db.flush()

        return {
            "voice_id": preset.voice_id,
            "voice_name": preset.voice_name,
            "voice_role": preset.voice_role,
            "is_default": True,
            "message": "音色切换成功",
        }

    # ========== 家庭音色库接口 (1.2) ==========
    @staticmethod
    async def create_voice_preset(
        db: AsyncSession,
        user_id: int,
        voice_role: str,
        voice_name: str | None = None,
        audio_url: str | None = None,
        duration_ms: int | None = None,
        similarity_score: float | None = None,
        is_default: bool = False,
        audio_data: str | None = None,
    ) -> dict:
        """创建音色库记录（调用外部克隆API）"""
        family = await FamilyService._get_user_family_obj(db, user_id)

        # 如果提供了音频数据，先调用外部克隆API
        external_voice_id = None
        if audio_data:
            try:
                clone_result = await VoiceCloneAPIClient.clone_voice(
                    audio_data=audio_data,
                    voice_name=voice_name,
                )
                # 外部API返回 {"uri": "speech:leijun:xxx:4928cf2f"}
                external_voice_id = clone_result.get("uri")
                if similarity_score is None and clone_result.get("similarity_score"):
                    similarity_score = clone_result.get("similarity_score")
            except httpx.HTTPStatusError as e:
                logger.error(f"Voice clone API HTTP error: {e.response.status_code}")
                raise ExternalApiException(f"克隆失败: {e.response.status_code}")
            except httpx.TimeoutException:
                logger.error("Voice clone API timeout")
                raise ExternalApiException("克隆超时，请重试")
            except Exception as e:
                logger.warning(f"Voice clone API call failed: {e}")

        # 如果设为默认，先取消其他默认
        if is_default:
            await db.execute(
                text("UPDATE family_voice_presets SET is_default=0 WHERE family_id=:family_id AND is_default=1")
                .bindparams(family_id=family.id)
            )

        # 生成唯一voice_id（优先使用外部返回的ID）
        voice_id = external_voice_id or uuid.uuid4().hex[:16]

        preset = FamilyVoicePreset(
            family_id=family.id,
            voice_id=voice_id,
            voice_role=voice_role,
            voice_name=voice_name,
            audio_url=audio_url,
            duration_ms=duration_ms,
            similarity_score=similarity_score,
            is_default=1 if is_default else 0,
        )
        db.add(preset)
        await db.flush()

        # 刷新对象以加载服务器生成的值（created_at, updated_at）
        await db.refresh(preset)

        return {
            'id': preset.id,
            'family_id': preset.family_id,
            'voice_id': preset.voice_id,
            'voice_role': preset.voice_role,
            'voice_name': preset.voice_name,
            'audio_url': preset.audio_url,
            'duration_ms': preset.duration_ms,
            'similarity_score': float(preset.similarity_score) if preset.similarity_score else None,
            'is_default': bool(preset.is_default),
            'created_at': preset.created_at.isoformat() if preset.created_at else None,
        }

    @staticmethod
    async def create_voice_preset_by_upload(
        db: AsyncSession,
        user_id: int,
        voice_role: str,
        voice_name: str,
        text: str,
        is_default: bool = False,
        file_content: bytes | None = None,
        filename: str = "audio.mp3",
    ) -> dict:
        """上传音频文件克隆音色（文件上传方式）
        Args:
            file_content: 音频文件二进制内容
            voice_name: 音色名称（对应 external API 的 customName）
            text: 音频对应的文本（对应 external API 的 text）
        """
        import logging
        logger = logging.getLogger(__name__)

        family = await FamilyService._get_user_family_obj(db, user_id)
        logger.info(f"User {user_id} family_id: {family.id}, starting voice clone for: {voice_name}")

        # 调用外部克隆API
        external_voice_id = None
        clone_similarity_score = None
        if file_content:
            try:
                clone_result = await VoiceCloneAPIClient.clone_voice(
                    file_content=file_content,
                    custom_name=voice_name,
                    text=text,
                    filename=filename,
                )
                # 外部API返回 {"uri": "speech:leijun:xxx:4928cf2f"}
                external_voice_id = clone_result.get("uri")
                clone_similarity_score = clone_result.get("similarity_score")
                logger.info(f"Voice clone API success: voice_id={external_voice_id}")
            except httpx.HTTPStatusError as e:
                logger.error(f"Voice clone API HTTP error: {e.response.status_code} - {e.response.text}")
                raise ExternalApiException(f"克隆失败，外部服务返回错误: {e.response.status_code}")
            except httpx.TimeoutException:
                logger.error("Voice clone API timeout")
                raise ExternalApiException("克隆超时，请重试")
            except Exception as e:
                logger.error(f"Voice clone API call failed: {str(e)}")
                raise ExternalApiException(f"克隆失败: {str(e)}")

        # 如果设为默认，先取消其他默认
        if is_default:
            await db.execute(
                text("UPDATE family_voice_presets SET is_default=0 WHERE family_id=:family_id AND is_default=1")
                .bindparams(family_id=family.id)
            )

        # 生成唯一voice_id（优先使用外部返回的ID）
        voice_id = external_voice_id or uuid.uuid4().hex[:16]

        preset = FamilyVoicePreset(
            family_id=family.id,
            voice_id=voice_id,
            voice_role=voice_role,
            voice_name=voice_name,
            is_default=1 if is_default else 0,
            similarity_score=clone_similarity_score,
        )
        db.add(preset)
        await db.flush()

        # 刷新对象以加载服务器生成的值（created_at, updated_at）
        await db.refresh(preset)

        return {
            'id': preset.id,
            'family_id': preset.family_id,
            'voice_id': preset.voice_id,
            'voice_role': preset.voice_role,
            'voice_name': preset.voice_name,
            'similarity_score': float(preset.similarity_score) if preset.similarity_score else None,
            'is_default': bool(preset.is_default),
            'created_at': preset.created_at.isoformat() if preset.created_at else None,
        }

    @staticmethod
    async def get_voice_presets(db: AsyncSession, user_id: int) -> list[dict]:
        """获取音色库列表"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        query = select(FamilyVoicePreset).where(
            FamilyVoicePreset.family_id == family.id,
            FamilyVoicePreset.is_active == 1,
        ).order_by(FamilyVoicePreset.is_default.desc(), FamilyVoicePreset.sort_order, FamilyVoicePreset.created_at.desc())

        result = await db.execute(query)
        presets = result.scalars().all()
        return [
            {
                'id': p.id,
                'family_id': p.family_id,
                'voice_id': p.voice_id,
                'voice_role': p.voice_role,
                'voice_name': p.voice_name,
                'audio_url': p.audio_url,
                'duration_ms': p.duration_ms,
                'similarity_score': float(p.similarity_score) if p.similarity_score else None,
                'is_default': bool(p.is_default),
                'is_active': p.is_active,
                'sort_order': p.sort_order,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in presets
        ]

    @staticmethod
    async def get_voice_preset_by_id(db: AsyncSession, user_id: int, preset_id: int) -> dict:
        """获取单个音色库记录"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(
            select(FamilyVoicePreset).where(
                FamilyVoicePreset.id == preset_id,
                FamilyVoicePreset.family_id == family.id,
                FamilyVoicePreset.is_active == 1,
            )
        )
        preset = result.scalar_one_or_none()
        if not preset:
            raise NotFoundException('音色记录不存在')

        return {
            'id': preset.id,
            'family_id': preset.family_id,
            'voice_id': preset.voice_id,
            'voice_role': preset.voice_role,
            'voice_name': preset.voice_name,
            'audio_url': preset.audio_url,
            'duration_ms': preset.duration_ms,
            'similarity_score': float(preset.similarity_score) if preset.similarity_score else None,
            'is_default': bool(preset.is_default),
            'is_active': preset.is_active,
            'sort_order': preset.sort_order,
            'created_at': preset.created_at.isoformat() if preset.created_at else None,
            'updated_at': preset.updated_at.isoformat() if preset.updated_at else None,
        }

    @staticmethod
    async def update_voice_preset(
        db: AsyncSession,
        user_id: int,
        preset_id: int,
        voice_name: str | None = None,
        audio_url: str | None = None,
        duration_ms: int | None = None,
        similarity_score: float | None = None,
        is_default: bool | None = None,
    ) -> dict:
        """更新音色库记录"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(
            select(FamilyVoicePreset).where(
                FamilyVoicePreset.id == preset_id,
                FamilyVoicePreset.family_id == family.id,
                FamilyVoicePreset.is_active == 1,
            )
        )
        preset = result.scalar_one_or_none()
        if not preset:
            raise NotFoundException('音色记录不存在')

        # 如果设为默认，先取消其他默认
        if is_default:
            await db.execute(
                text("UPDATE family_voice_presets SET is_default=0 WHERE family_id=:family_id AND is_default=1")
                .bindparams(family_id=family.id)
            )

        if voice_name is not None:
            preset.voice_name = voice_name
        if audio_url is not None:
            preset.audio_url = audio_url
        if duration_ms is not None:
            preset.duration_ms = duration_ms
        if similarity_score is not None:
            preset.similarity_score = similarity_score
        if is_default is not None:
            preset.is_default = 1 if is_default else 0

        await db.flush()

        return {
            'id': preset.id,
            'voice_id': preset.voice_id,
            'voice_name': preset.voice_name,
            'is_default': bool(preset.is_default),
            'message': '更新成功',
        }

    @staticmethod
    async def delete_voice_preset(db: AsyncSession, user_id: int, preset_id: int) -> dict:
        """删除音色库记录(软删除)"""
        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(
            select(FamilyVoicePreset).where(
                FamilyVoicePreset.id == preset_id,
                FamilyVoicePreset.family_id == family.id,
                FamilyVoicePreset.is_active == 1,
            )
        )
        preset = result.scalar_one_or_none()
        if not preset:
            raise NotFoundException('音色记录不存在')

        # 先调用外部API删除音色
        try:
            await VoiceCloneAPIClient.delete_voice(preset.voice_id)
        except httpx.HTTPStatusError as e:
            logger.warning(f"Voice delete API HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.TimeoutException:
            logger.warning("Voice delete API timeout")
        except Exception as e:
            logger.warning(f"Voice delete API call failed: {e}")

        # 软删除本地记录
        preset.is_active = 0
        await db.flush()

        return {'message': '删除成功'}

    @staticmethod
    async def delete_voice_by_name(db: AsyncSession, user_id: int, voice_name: str) -> dict:
        """根据音色名称删除音色（只删除当前家庭的音色）
        Args:
            voice_name: 音色名称
        """
        import logging
        logger = logging.getLogger(__name__)

        family = await FamilyService._get_user_family_obj(db, user_id)
        result = await db.execute(
            select(FamilyVoicePreset).where(
                FamilyVoicePreset.voice_name == voice_name,
                FamilyVoicePreset.family_id == family.id,
                FamilyVoicePreset.is_active == 1,
            )
        )
        preset = result.scalar_one_or_none()
        if not preset:
            raise NotFoundException(f'音色"{voice_name}"不存在或不属于当前家庭')

        voice_id = preset.voice_id

        # 调用外部API删除音色
        try:
            await VoiceCloneAPIClient.delete_voice(voice_id)
            logger.info(f"Deleted voice from external API: {voice_id}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"Voice delete API HTTP error: {e.response.status_code}")
        except httpx.TimeoutException:
            logger.warning("Voice delete API timeout")
        except Exception as e:
            logger.warning(f"Voice delete API call failed: {e}")

        # 软删除本地记录
        preset.is_active = 0
        await db.flush()

        return {'message': f'音色"{voice_name}"删除成功', 'voice_id': voice_id}

    @staticmethod
    async def text_to_speech(
        db: AsyncSession,
        user_id: int,
        baby_id: int,
        text: str,
        voice_id: str | None = None,
    ) -> dict:
        """语音合成（TTS）
        Args:
            voice_id: 音色ID，如果为空则使用当前默认音色
        """
        import logging
        logger = logging.getLogger(__name__)

        # 获取或查找默认音色
        if not voice_id:
            family = await FamilyService._get_user_family_obj(db, user_id)
            result = await db.execute(
                select(FamilyVoicePreset).where(
                    FamilyVoicePreset.family_id == family.id,
                    FamilyVoicePreset.is_default == 1,
                    FamilyVoicePreset.is_active == 1,
                )
            )
            preset = result.scalar_one_or_none()
            if not preset:
                raise NotFoundException('未找到默认音色，请先克隆或选择一个音色')
            voice_id = preset.voice_id
        else:
            # 验证音色存在
            family = await FamilyService._get_user_family_obj(db, user_id)
            result = await db.execute(
                select(FamilyVoicePreset).where(
                    FamilyVoicePreset.voice_id == voice_id,
                    FamilyVoicePreset.family_id == family.id,
                    FamilyVoicePreset.is_active == 1,
                )
            )
            preset = result.scalar_one_or_none()
            if not preset:
                raise NotFoundException('音色记录不存在')

        # 调用外部TTS API
        try:
            audio_bytes = await VoiceCloneAPIClient.generate_speech(
                input_text=text,
                voice=voice_id,
                response_format="wav",
                sample_rate=24000,
                speed=1.0,
            )
            logger.info(f"TTS success for voice: {voice_id}")
        except httpx.HTTPStatusError as e:
            logger.error(f"TTS API HTTP error: {e.response.status_code} - {e.response.text}")
            raise ExternalApiException(f"语音合成失败，外部服务返回错误: {e.response.status_code}")
        except httpx.TimeoutException:
            logger.error("TTS API timeout")
            raise ExternalApiException("语音合成超时，请重试")
        except Exception as e:
            logger.error(f"TTS API call failed: {str(e)}")
            raise ExternalApiException(f"语音合成失败: {str(e)}")

        return {
            'baby_id': baby_id,
            'voice_id': voice_id,
            'voice_name': preset.voice_name,
            'audio_data': audio_bytes.hex(),  # 返回十六进制编码的音频数据
            'text': text,
        }


voice_service = VoiceService()


class VoiceCloneAPIClient:
    """语音克隆API客户端"""

    BASE_URL = "http://223.247.96.246:30028/v1/audio"

    @classmethod
    async def clone_voice(
        cls,
        file_content: bytes,
        custom_name: str,
        text: str,
        filename: str = "audio.mp3",
    ) -> dict:
        """调用克隆音色接口 POST /v1/audio/clone_voice
        Args:
            file_content: 音频文件二进制内容
            custom_name: 自定义音色名称
            text: 对应的文本内容
            filename: 文件名（支持 mp3/wav/m4a 等格式）
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {
                "file": (filename, file_content, f"audio/{filename.split('.')[-1]}"),
            }
            data = {
                "customName": custom_name,
                "text": text,
            }
            response = await client.post(
                f"{cls.BASE_URL}/clone_voice",
                files=files,
                data=data,
            )
            response.raise_for_status()
            return response.json()

    @classmethod
    async def train_voice(cls, audio_data: str, voice_role: str = "custom") -> dict:
        """调用训练音色接口 POST /v1/audio/train"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{cls.BASE_URL}/train",
                json={
                    "audio_data": audio_data,
                    "voice_role": voice_role,
                }
            )
            response.raise_for_status()
            return response.json()

    @classmethod
    async def list_voices(cls, family_id: int | None = None) -> dict:
        """调用获取音色列表接口 GET /v1/audio/list"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {}
            if family_id:
                params["family_id"] = family_id
            response = await client.get(
                f"{cls.BASE_URL}/list",
                params=params
            )
            response.raise_for_status()
            return response.json()

    @classmethod
    async def delete_voice(cls, voice_id: str) -> dict:
        """调用删除音色接口 DELETE /v1/audio/delete_voice"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{cls.BASE_URL}/delete_voice",
                params={"voice_id": voice_id}
            )
            response.raise_for_status()
            return response.json()

    @classmethod
    async def generate_speech(
        cls,
        input_text: str,
        voice: str,
        response_format: str = "wav",
        sample_rate: int = 24000,
        speed: float = 1.0,
    ) -> bytes:
        """调用语音合成接口 POST /v1/audio/generate_speech
        Args:
            input_text: 要转换的文本
            voice: 音色ID（voice_id）
            response_format: 音频格式（wav/mp3）
            sample_rate: 采样率
            speed: 语速
        Returns:
            音频二进制数据
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{cls.BASE_URL}/generate_speech",
                json={
                    "input": input_text,
                    "voice": voice,
                    "response_format": response_format,
                    "sample_rate": sample_rate,
                    "stream": False,
                    "speed": speed,
                }
            )
            response.raise_for_status()
            return response.content