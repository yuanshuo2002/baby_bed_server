"""
自主对话路由
包含语音克隆、音色切换、ASR、TTS、LLM对话、长记忆等接口
"""
import json
import re
from typing import Any

import httpx
from fastapi import APIRouter, Body, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.exceptions import BusinessException
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.services.ltm_service import ltm_service
from app.schemas.voice import (
    VoiceSwitch, ASRRequest, TTSRequest, ChatRequest,
    WakeRequest, WakeResponse, IntentRequest, IntentResponse,
    CommandRequest, CommandResponse, LTMQueryRequest, LTMStoreRequest,
    SessionCreateRequest, SessionInfo,
    VoiceCloneTrainRequest, VoiceCloneTrainResponse, VoiceInfo, VoiceSwitchRequest,
    FamilyVoicePresetCreate, FamilyVoicePresetUpdate, FamilyVoicePresetInfo,
)
from app.services.voice_service import VoiceCloneAPIClient, voice_service
from config import settings

router = APIRouter(prefix="/voice", tags=["自主对话"])


def not_implemented(message: str) -> None:
    raise BusinessException(code=501, message=message, status_code=501)


def _strip_json_fence(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    return content.strip()


def _extract_asr_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload.strip()

    if not isinstance(payload, dict):
        return ""

    for key in ("text", "result", "transcript"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("text", "result", "transcript"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


async def _call_chat_llm(system_prompt: str, user_prompt: str) -> str:
    api_url = settings.VOICE_CHAT_LLM_API_URL or settings.LLM_API_URL
    api_key = settings.VOICE_CHAT_LLM_API_KEY or settings.LLM_API_KEY
    model_name = settings.VOICE_CHAT_LLM_MODEL or settings.LLM_MODEL or "gemma4:latest"

    if not api_url:
        raise BusinessException(code=503, message="LLM服务未配置", status_code=503)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

    return (
        result.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )


async def _call_json_llm(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    content = await _call_chat_llm(system_prompt, user_prompt)
    content = _strip_json_fence(content)
    return json.loads(content)


def _fallback_intent(text: str) -> dict[str, Any]:
    lowered = text.lower()
    if any(keyword in text for keyword in ["哭", "危险", "报警", "救命"]):
        return {"intent": "emergency", "confidence": 0.72, "slots": {"priority": "high"}}
    if any(keyword in text for keyword in ["开灯", "关灯", "灯光", "亮一点"]):
        return {"intent": "device_control", "confidence": 0.68, "slots": {"device": "light"}}
    if any(keyword in text for keyword in ["放歌", "音乐", "儿歌", "暂停音乐"]):
        return {"intent": "music", "confidence": 0.68, "slots": {"device": "music"}}
    if any(keyword in text for keyword in ["睡", "醒", "状态", "睡眠"]):
        return {"intent": "sleep_status", "confidence": 0.65, "slots": {"topic": "sleep"}}
    if any(keyword in lowered for keyword in ["monitor", "camera", "video"]):
        return {"intent": "monitor", "confidence": 0.65, "slots": {"device": "monitor"}}
    return {"intent": "chat", "confidence": 0.55, "slots": {}}


def _command_result(command: str, params: dict[str, Any] | None) -> dict[str, Any]:
    normalized = (command or "").strip().lower()
    if normalized in {"light", "lights", "lamp"}:
        action = (params or {}).get("action", "toggle")
        return {"command": "light", "status": "pending", "result": f"light:{action}", "message": "灯光指令已受理，等待设备侧执行"}
    if normalized in {"music", "audio"}:
        action = (params or {}).get("action", "play")
        return {"command": "music", "status": "pending", "result": f"music:{action}", "message": "音乐指令已受理，等待设备侧执行"}
    if normalized in {"monitor", "camera"}:
        action = (params or {}).get("action", "open")
        return {"command": "monitor", "status": "pending", "result": f"monitor:{action}", "message": "监护指令已受理，等待设备侧执行"}
    if normalized in {"sleep_status", "routine", "comfort"}:
        return {"command": normalized, "status": "success", "result": normalized, "message": "语义指令已解析，可继续接入具体业务动作"}
    return {"command": command, "status": "success", "result": command, "message": "指令已解析"}


async def _proxy_asr(body: ASRRequest) -> dict[str, Any]:
    if not settings.ASR_API_URL:
        raise BusinessException(code=503, message="ASR服务未配置", status_code=503)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            settings.ASR_API_URL,
            json={"baby_id": body.baby_id, "audio_data": body.audio_data},
        )
        response.raise_for_status()
        payload = response.json()

    text = _extract_asr_text(payload)
    if not text:
        raise BusinessException(code=502, message="ASR服务未返回可用文本", status_code=502)

    return {"text": text, "raw": payload}


@router.post("/clone", response_model=ApiResponse, summary="上传语音进行克隆")
async def clone_voice(
    baby_id: int = Form(..., description="宝宝ID"),
    clip_name: str = Form(..., description="语音片段名称"),
    audio_file: UploadFile = File(..., description="音频文件"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """上传家长语音片段，调用讯飞语音克隆API生成音色"""
    # TODO: 文件上传存储 + 调用克隆API
    audio_url = f"/uploads/voice/{audio_file.filename}"
    result = await voice_service.clone_voice(db, user_id=current_user.id, baby_id=baby_id, clip_name=clip_name, audio_url=audio_url)
    return success(data=result, message="语音克隆任务已提交")


@router.get("/clips", response_model=ApiResponse, summary="获取语音片段列表")
async def get_voice_clips(
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取指定宝宝的所有语音片段列表"""
    result = await voice_service.get_voice_clips(db, user_id=current_user.id, baby_id=baby_id)
    return success(data=result)


@router.delete("/clip/{clip_id}", response_model=ApiResponse, summary="删除语音片段")
async def delete_voice_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """删除指定的语音片段"""
    await voice_service.delete_voice_clip(db, user_id=current_user.id, clip_id=clip_id)
    return success(message="删除成功")


@router.post("/chat", response_model=ApiResponse, summary="LLM对话")
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """与LLM进行对话，支持上下文记忆"""
    result = await voice_service.chat(
        db, user_id=current_user.id,
        baby_id=body.baby_id, message=body.message, session_id=body.session_id,
    )
    return success(data=result)


@router.get("/history", response_model=ApiResponse, summary="获取对话历史")
async def get_chat_history(
    baby_id: int,
    session_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取宝宝的对话历史记录"""
    result = await voice_service.get_chat_history(db, user_id=current_user.id, baby_id=baby_id, session_id=session_id)
    return success(data=result)


@router.post("/session", response_model=ApiResponse, summary="创建会话")
async def create_session(
    body: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """创建新的对话会话"""
    result = await voice_service.create_session(
        db, user_id=current_user.id, baby_id=body.baby_id, session_type=body.session_type,
    )
    return success(data=result, message="会话创建成功")


@router.post("/session/{session_id}/close", response_model=ApiResponse, summary="关闭会话")
async def close_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """关闭指定的对话会话"""
    result = await voice_service.close_session(db, user_id=current_user.id, session_id=session_id)
    return success(data=result, message="会话已关闭")


@router.post("/switch", response_model=ApiResponse, summary="切换音色")
async def switch_voice(
    body: VoiceSwitchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """切换默认音色，将指定音色设为当前家庭的默认音色"""
    result = await voice_service.switch_voice(db, user_id=current_user.id, voice_id=body.voice_id)
    return success(data=result, message="音色切换成功")


@router.get("/current", response_model=ApiResponse, summary="获取当前生效音色")
async def get_current_voice(
    baby_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前家庭生效中的音色

    当前版本返回家庭默认音色；
    `baby_id` 为后续扩展宝宝级音色策略预留。
    """
    result = await voice_service.get_current_voice(
        db,
        user_id=current_user.id,
        baby_id=baby_id,
    )
    return success(data=result, message="获取当前音色成功")


@router.post("/tts", response_model=ApiResponse, summary="语音合成(TTS)")
async def text_to_speech(
    body: TTSRequest | None = Body(None),
    baby_id: int | None = Form(None, description="宝宝ID"),
    text: str | None = Form(None, description="待合成文本"),
    voice_id: str | None = Form(None, description="音色ID（可选，不传则使用默认音色）"),
    voice_role: str | None = Form(None, description="音色角色（可选，不传则使用默认音色）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """将文本转换为语音，使用克隆的音色
    - 如果传入 voice_id，使用指定的音色
    - 如果传入 voice_role，优先按角色匹配家庭音色
    - 如果不传 voice_id，使用当前默认音色
    """
    resolved_baby_id = baby_id if baby_id is not None else (body.baby_id if body else None)
    resolved_text = text if text is not None else (body.text if body else None)
    resolved_voice_id = voice_id
    resolved_voice_role = voice_role if voice_role is not None else (body.voice_role if body else None)

    if resolved_baby_id is None or not resolved_text:
        raise BusinessException(code=422, message="baby_id 和 text 不能为空", status_code=422)

    result = await voice_service.text_to_speech(
        db,
        user_id=current_user.id,
        baby_id=resolved_baby_id,
        text=resolved_text,
        voice_id=resolved_voice_id,
        voice_role=resolved_voice_role,
    )
    return success(data=result, message="语音合成成功")


@router.post("/asr", response_model=ApiResponse, summary="语音识别")
async def speech_to_text(body: ASRRequest):
    result = await _proxy_asr(body)
    return success(data=result, message="语音识别成功")


@router.post("/wake", response_model=ApiResponse, summary="唤醒词检测")
async def wake_word(body: WakeRequest):
    transcript = ""
    try:
        asr_result = await _proxy_asr(ASRRequest(baby_id=body.baby_id, audio_data=body.audio_data))
        transcript = asr_result["text"]
    except Exception:
        transcript = ""

    wake_words = ["小床", "宝宝床", "小宝", "bed", "gemma"]
    matched = next((word for word in wake_words if word.lower() in transcript.lower()), None)
    confidence = 0.96 if matched else (0.45 if transcript else 0.2)

    result = {
        "is_waked": bool(matched),
        "confidence": confidence,
        "wake_word": matched,
        "transcript": transcript,
    }
    return success(data=result, message="唤醒检测完成")


@router.post("/intent", response_model=ApiResponse, summary="意图识别")
async def detect_intent(body: IntentRequest):
    system_prompt = (
        "你是婴儿床语音助手的NLU模块。"
        "请只返回JSON，格式为"
        '{"intent":"chat|comfort|sleep_status|device_control|music|monitor|routine|emergency|unknown",'
        '"confidence":0.0,"slots":{}}。'
        "不要输出任何额外解释。"
    )
    user_prompt = f"用户文本：{body.text}\n上下文：{body.context or '无'}"

    try:
        result = await _call_json_llm(system_prompt, user_prompt)
    except Exception:
        result = _fallback_intent(body.text)

    normalized = {
        "intent": str(result.get("intent") or "unknown"),
        "confidence": float(result.get("confidence") or 0.5),
        "slots": result.get("slots") or {},
    }
    return success(data=normalized, message="意图识别成功")


@router.post("/command", response_model=ApiResponse, summary="语音指令执行")
async def execute_command(body: CommandRequest):
    result = _command_result(body.command, body.params)
    return success(data=result, message="指令已处理")


@router.post("/ltm/query", response_model=ApiResponse, summary="查询长记忆")
async def query_ltm(body: LTMQueryRequest):
    result = await ltm_service.ask(question=body.query, profile_id=body.baby_id)
    answer = result.get("answer", "")
    related_events = result.get("related_events", [])[: body.limit]

    items: list[dict[str, Any]] = []
    if answer:
        items.append(
            {
                "id": 0,
                "baby_id": body.baby_id,
                "content": answer,
                "tags": "ltm_answer",
                "source": "ltm_ask",
                "created_at": None,
            }
        )

    for idx, event in enumerate(related_events, start=1):
        items.append(
            {
                "id": idx,
                "baby_id": body.baby_id,
                "content": event.get("summary") or event.get("keywords") or json.dumps(event, ensure_ascii=False),
                "tags": event.get("event_type") or event.get("risk"),
                "source": "ltm_event",
                "created_at": event.get("date") or event.get("start_time"),
            }
        )

    return success(data=items[: body.limit], message="长记忆查询成功")


@router.post("/ltm/store", response_model=ApiResponse, summary="存储长记忆")
async def store_ltm(body: LTMStoreRequest):
    result = await ltm_service.upload_event(description=body.content, profile_id=body.baby_id)
    return success(
        data={
            "id": result.get("event_id"),
            "detected_type": result.get("detected_type"),
            "message": result.get("message", "success"),
            "tags": body.tags or [],
            "source": body.source,
        },
        message="长记忆存储成功",
    )


@router.post("/clone/train", response_model=ApiResponse, summary="训练语音克隆模型")
async def train_clone(body: VoiceCloneTrainRequest):
    result = await VoiceCloneAPIClient.train_voice(audio_data=body.audio_data, voice_role=body.voice_role)
    data = {
        "voice_id": result.get("voice_id") or result.get("uri") or "",
        "voice_role": body.voice_role,
        "status": result.get("status", "completed"),
        "similarity_score": result.get("similarity_score"),
        "message": result.get("message", "训练任务已提交"),
        "created_at": result.get("created_at"),
    }
    return success(data=data, message="语音克隆训练已提交")


@router.get("/clone/voices", response_model=ApiResponse, summary="获取旧版音色库列表")
async def clone_voice_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await voice_service.get_voice_presets(db, user_id=current_user.id)
    return success(data=result, message="获取音色库成功")


@router.put("/clone/voices/{voice_id}/default", response_model=ApiResponse, summary="设置旧版默认音色")
async def clone_voice_default(
    voice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await voice_service.switch_voice(db, user_id=current_user.id, voice_id=voice_id)
    return success(data=result, message="默认音色切换成功")


# ========== 家庭音色库接口 (1.2) ==========
@router.post("/library/upload", response_model=ApiResponse, summary="上传音频克隆音色")
async def create_voice_preset_by_upload(
    voice_role: str = Form(..., description="角色: mom/dad/nanny/other"),
    voice_name: str = Form(..., description="音色名称"),
    text: str = Form(..., description="音频对应的文本内容"),
    is_default: bool = Form(default=False, description="是否设为默认"),
    audio_file: UploadFile = File(..., description="音频文件(支持mp3/wav)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """上传音频文件进行克隆，自动调用外部API并保存到数据库"""
    # 读取文件内容
    file_content = await audio_file.read()
    file_ext = audio_file.filename.split(".")[-1] if audio_file.filename else "mp3"

    result = await voice_service.create_voice_preset_by_upload(
        db,
        user_id=current_user.id,
        voice_role=voice_role,
        voice_name=voice_name,
        text=text,
        is_default=is_default,
        file_content=file_content,
        filename=audio_file.filename or f"audio.{file_ext}",
    )
    return success(data=result, message="音色克隆成功")


@router.post("/library", response_model=ApiResponse, summary="创建音色库记录")
async def create_voice_preset(
    body: FamilyVoicePresetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """创建音色库记录，支持多角色音色管理（手动指定voice_id，不调用克隆API）"""
    result = await voice_service.create_voice_preset(
        db,
        user_id=current_user.id,
        voice_role=body.voice_role,
        voice_name=body.voice_name,
        audio_data=body.audio_data,
        audio_url=body.audio_url,
        duration_ms=body.duration_ms,
        similarity_score=body.similarity_score,
        is_default=body.is_default,
    )
    return success(data=result, message="音色库记录创建成功")


@router.get("/library", response_model=ApiResponse, summary="获取音色库列表")
async def get_voice_presets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前家庭的所有音色库列表"""
    result = await voice_service.get_voice_presets(db, user_id=current_user.id)
    return success(data=result)


@router.get("/library/{preset_id}", response_model=ApiResponse, summary="获取音色库记录")
async def get_voice_preset(
    preset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取指定的音色库记录"""
    result = await voice_service.get_voice_preset_by_id(db, user_id=current_user.id, preset_id=preset_id)
    return success(data=result)


@router.delete("/library/by-name/{voice_name}", response_model=ApiResponse, summary="根据音色名称删除音色")
async def delete_voice_by_name(
    voice_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """根据音色名称删除音色（只删除当前家庭的音色）
    - 调用外部API删除对应voice_id的音色
    - 软删除本地记录
    """
    result = await voice_service.delete_voice_by_name(db, user_id=current_user.id, voice_name=voice_name)
    return success(message=result['message'])


@router.put("/library/{preset_id}", response_model=ApiResponse, summary="更新音色库记录")
async def update_voice_preset(
    preset_id: int,
    body: FamilyVoicePresetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """更新指定的音色库记录"""
    result = await voice_service.update_voice_preset(
        db,
        user_id=current_user.id,
        preset_id=preset_id,
        voice_name=body.voice_name,
        audio_url=body.audio_url,
        duration_ms=body.duration_ms,
        similarity_score=body.similarity_score,
        is_default=body.is_default,
    )
    return success(data=result, message="音色库记录更新成功")


@router.delete("/library/{preset_id}", response_model=ApiResponse, summary="删除音色库记录")
async def delete_voice_preset(
    preset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """删除指定的音色库记录(软删除)"""
    result = await voice_service.delete_voice_preset(db, user_id=current_user.id, preset_id=preset_id)
    return success(message=result['message'])
