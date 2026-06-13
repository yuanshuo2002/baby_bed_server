"""
自主对话路由
包含语音克隆、音色切换、ASR、TTS、LLM对话、长记忆等接口
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.voice import (
    VoiceSwitch, ASRRequest, TTSRequest, ChatRequest,
    WakeRequest, WakeResponse, IntentRequest, IntentResponse,
    CommandRequest, CommandResponse, LTMQueryRequest, LTMStoreRequest,
    SessionCreateRequest, SessionInfo,
    VoiceCloneTrainRequest, VoiceCloneTrainResponse, VoiceInfo, VoiceSwitchRequest,
    FamilyVoicePresetCreate, FamilyVoicePresetUpdate, FamilyVoicePresetInfo,
)
from app.services.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["自主对话"])


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


@router.post("/tts", response_model=ApiResponse, summary="语音合成(TTS)")
async def text_to_speech(
    baby_id: int = Form(..., description="宝宝ID"),
    text: str = Form(..., description="待合成文本"),
    voice_id: str | None = Form(None, description="音色ID（可选，不传则使用默认音色）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """将文本转换为语音，使用克隆的音色
    - 如果传入 voice_id，使用指定的音色
    - 如果不传 voice_id，使用当前默认音色
    """
    result = await voice_service.text_to_speech(
        db,
        user_id=current_user.id,
        baby_id=baby_id,
        text=text,
        voice_id=voice_id,
    )
    return success(data=result, message="语音合成成功")


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