"""
本地 MeloTTS 语音合成服务

可独立运行，例如：
    uvicorn app.services.melotts_tts_app:app --host 0.0.0.0 --port 40028
"""
from __future__ import annotations

import inspect
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, model_validator

try:
    from melo.api import TTS as MeloTTS
except Exception as exc:  # pragma: no cover - import failure should be explicit at runtime
    MeloTTS = None
    _melo_import_error = exc
else:
    _melo_import_error = None


APP_NAME = os.getenv("MELOTTS_APP_NAME", "MeloTTS Local Service")
DEFAULT_LANGUAGE = os.getenv("MELOTTS_LANGUAGE", "ZH")
DEFAULT_DEVICE = os.getenv("MELOTTS_DEVICE", "cpu")
DEFAULT_SPEAKER = os.getenv("MELOTTS_DEFAULT_SPEAKER", "ZH")
DEFAULT_OUTPUT_FORMAT = os.getenv("MELOTTS_OUTPUT_FORMAT", "wav")
DEFAULT_SAMPLE_RATE = int(os.getenv("MELOTTS_SAMPLE_RATE", "24000"))
DEFAULT_SPEED = float(os.getenv("MELOTTS_SPEED", "1.0"))

ROLE_SPEAKER_MAP = {
    "mom": os.getenv("MELOTTS_SPEAKER_MOM", DEFAULT_SPEAKER),
    "dad": os.getenv("MELOTTS_SPEAKER_DAD", DEFAULT_SPEAKER),
    "nanny": os.getenv("MELOTTS_SPEAKER_NANNY", DEFAULT_SPEAKER),
    "other": os.getenv("MELOTTS_SPEAKER_OTHER", DEFAULT_SPEAKER),
}

app = FastAPI(title=APP_NAME)


class TTSRequest(BaseModel):
    input: str | None = Field(None, description="待合成文本")
    text: str | None = Field(None, description="兼容字段：待合成文本")
    speaker: str | None = Field(None, description="声线/音色标识")
    voice: str | None = Field(None, description="兼容字段：声线/音色标识")
    voice_role: str | None = Field(None, description="兼容字段：角色名")
    response_format: str = Field(default=DEFAULT_OUTPUT_FORMAT, description="wav/mp3")
    sample_rate: int = Field(default=DEFAULT_SAMPLE_RATE, ge=8000, le=48000)
    stream: bool = Field(default=False, description="兼容字段：是否流式")
    speed: float = Field(default=DEFAULT_SPEED, ge=0.5, le=2.0)
    language: str | None = Field(default=None, description="语言（可选）")

    @model_validator(mode="before")
    @classmethod
    def _populate_input(cls, data):
        if isinstance(data, dict):
            if not data.get("input") and data.get("text"):
                data["input"] = data["text"]
        return data


def _build_tts() -> MeloTTS:
    if MeloTTS is None:
        raise RuntimeError(f"无法导入 MeloTTS: {_melo_import_error}")

    kwargs: dict[str, object] = {}
    params = inspect.signature(MeloTTS).parameters
    if "language" in params:
        kwargs["language"] = DEFAULT_LANGUAGE
    if "device" in params:
        kwargs["device"] = DEFAULT_DEVICE
    if "progress" in params:
        kwargs["progress"] = False
    if "model_dir" in params:
        model_dir = os.getenv("MELOTTS_MODEL_DIR")
        if model_dir:
            kwargs["model_dir"] = model_dir
    if "config_path" in params:
        config_path = os.getenv("MELOTTS_CONFIG_PATH")
        if config_path:
            kwargs["config_path"] = config_path

    attempts = [
        lambda: MeloTTS(**kwargs),
        lambda: MeloTTS(DEFAULT_LANGUAGE, DEFAULT_DEVICE),
        lambda: MeloTTS(DEFAULT_LANGUAGE),
        lambda: MeloTTS(),
    ]
    last_type_error: TypeError | None = None
    for attempt in attempts:
        try:
            return attempt()
        except TypeError as exc:
            last_type_error = exc
            continue

    raise RuntimeError(f"无法初始化 MeloTTS: {last_type_error}")


TTS_MODEL = _build_tts()


def _resolve_speaker(request: TTSRequest) -> str:
    candidate = request.speaker or request.voice or request.voice_role
    if not candidate:
        return DEFAULT_SPEAKER
    return ROLE_SPEAKER_MAP.get(candidate, candidate)


def _synthesize_to_file(text: str, speaker: str, speed: float, output_path: Path) -> None:
    method = getattr(TTS_MODEL, "tts_to_file", None)
    if method is None:
        raise RuntimeError("MeloTTS 模型对象没有 tts_to_file 方法")

    params = inspect.signature(method).parameters
    kwargs: dict[str, object] = {}
    for name in params:
        if name in {"text", "input", "sentence"}:
            kwargs[name] = text
        elif name in {"speaker", "speaker_id", "spk", "voice", "voice_id"}:
            kwargs[name] = speaker
        elif name in {"speed", "rate"}:
            kwargs[name] = speed
        elif name in {"file_path", "path", "output_path", "save_path"}:
            kwargs[name] = str(output_path)

    attempts = [
        lambda: method(**kwargs),
        lambda: method(text, speaker, str(output_path)),
        lambda: method(text, speaker, str(output_path), speed),
        lambda: method(text, str(output_path)),
        lambda: method(text),
    ]

    last_type_error: TypeError | None = None
    for attempt in attempts:
        try:
            attempt()
            return
        except TypeError as exc:
            last_type_error = exc
            continue
    raise RuntimeError(f"MeloTTS 调用失败: {last_type_error}")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "language": DEFAULT_LANGUAGE,
        "device": DEFAULT_DEVICE,
        "default_speaker": DEFAULT_SPEAKER,
        "output_format": DEFAULT_OUTPUT_FORMAT,
    }


@app.post("/tts")
def tts(payload: TTSRequest):
    text = (payload.input or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="input/text 不能为空")

    speaker = _resolve_speaker(payload)
    output_format = (payload.response_format or DEFAULT_OUTPUT_FORMAT).lower()
    if output_format not in {"wav", "mp3"}:
        raise HTTPException(status_code=422, detail="response_format 仅支持 wav/mp3")

    with tempfile.TemporaryDirectory(prefix="melotts_") as tmpdir:
        output_path = Path(tmpdir) / f"tts.{output_format}"
        _synthesize_to_file(
            text=text,
            speaker=speaker,
            speed=payload.speed,
            output_path=output_path,
        )

        if not output_path.exists():
            raise HTTPException(status_code=500, detail="TTS 合成完成但未生成音频文件")

        audio_bytes = output_path.read_bytes()

    media_type = "audio/wav" if output_format == "wav" else "audio/mpeg"
    return Response(content=audio_bytes, media_type=media_type)


@app.post("/tts/json")
def tts_json(payload: TTSRequest):
    text = (payload.input or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="input/text 不能为空")

    speaker = _resolve_speaker(payload)
    output_format = (payload.response_format or DEFAULT_OUTPUT_FORMAT).lower()
    if output_format not in {"wav", "mp3"}:
        raise HTTPException(status_code=422, detail="response_format 仅支持 wav/mp3")

    with tempfile.TemporaryDirectory(prefix="melotts_") as tmpdir:
        output_path = Path(tmpdir) / f"tts.{output_format}"
        _synthesize_to_file(
            text=text,
            speaker=speaker,
            speed=payload.speed,
            output_path=output_path,
        )

        if not output_path.exists():
            raise HTTPException(status_code=500, detail="TTS 合成完成但未生成音频文件")

        audio_bytes = output_path.read_bytes()

    import base64

    return JSONResponse(
        {
            "success": True,
            "speaker": speaker,
            "response_format": output_format,
            "sample_rate": payload.sample_rate,
            "speed": payload.speed,
            "audio_data": base64.b64encode(audio_bytes).decode("utf-8"),
        }
    )
