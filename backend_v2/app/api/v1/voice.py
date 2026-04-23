"""
MindPal Backend V2 - Voice API
语音服务API端点
"""

import base64
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_user_id
from app.models import User, Player
from app.services.voice.tts import TTSService, TTSConfig, VoiceType, get_tts_service
from app.services.voice.asr import ASRService, ASRConfig, ASRFormat, get_asr_service
from app.schemas import APIResponse


router = APIRouter()


# ==================== Schemas ====================

class TTSRequest(BaseModel):
    """TTS请求"""
    text: str = Field(..., min_length=1, max_length=2000, description="要合成的文本")
    voice: Optional[str] = Field(None, description="语音类型")
    format: Optional[str] = Field("mp3", description="输出格式: mp3, wav, pcm")
    sample_rate: Optional[int] = Field(16000, description="采样率: 8000, 16000, 24000")
    volume: Optional[int] = Field(50, ge=0, le=100, description="音量: 0-100")
    speech_rate: Optional[int] = Field(0, ge=-500, le=500, description="语速: -500到500")
    pitch_rate: Optional[int] = Field(0, ge=-500, le=500, description="音调: -500到500")


class TTSNPCRequest(BaseModel):
    """NPC TTS请求"""
    text: str = Field(..., min_length=1, max_length=2000, description="要合成的文本")
    npc_id: str = Field(..., description="NPC ID")


class ASRRequest(BaseModel):
    """ASR请求 (Base64音频)"""
    audio_base64: str = Field(..., description="Base64编码的音频数据")
    format: Optional[str] = Field("wav", description="音频格式: wav, mp3, pcm")
    sample_rate: Optional[int] = Field(16000, description="采样率")


class ASRResponse(BaseModel):
    """ASR响应"""
    text: str = Field(..., description="识别的文本")
    confidence: float = Field(..., description="置信度")
    duration: float = Field(0, description="音频时长(秒)")


class VoiceInfo(BaseModel):
    """语音信息"""
    id: str
    name: str
    gender: str
    description: str


# ==================== TTS Endpoints ====================

@router.post("/tts", response_class=Response)
async def text_to_speech(
    request: TTSRequest,
    current_user: int = Depends(get_current_user_id),
):
    """
    文本转语音

    将文本转换为音频，返回音频文件
    """
    tts = get_tts_service()

    # 构建配置
    voice = VoiceType.XIAOYUN
    if request.voice:
        try:
            voice = VoiceType(request.voice)
        except ValueError:
            pass

    config = TTSConfig(
        voice=voice,
        format=request.format or "mp3",
        sample_rate=request.sample_rate or 16000,
        volume=request.volume or 50,
        speech_rate=request.speech_rate or 0,
        pitch_rate=request.pitch_rate or 0,
    )

    # 合成
    audio_data = await tts.synthesize(request.text, config)

    if not audio_data:
        raise HTTPException(
            status_code=503,
            detail="TTS service unavailable or synthesis failed"
        )

    # 设置Content-Type
    content_type_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "pcm": "audio/pcm",
    }
    content_type = content_type_map.get(config.format, "audio/mpeg")

    return Response(
        content=audio_data,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename=tts_output.{config.format}"
        }
    )


@router.post("/tts/npc", response_class=Response)
async def npc_text_to_speech(
    request: TTSNPCRequest,
    current_user: int = Depends(get_current_user_id),
):
    """
    NPC语音合成

    使用NPC专属语音合成文本
    """
    tts = get_tts_service()

    # 获取NPC对应的语音
    voice = tts.get_voice_for_npc(request.npc_id)

    config = TTSConfig(voice=voice)

    # 合成
    audio_data = await tts.synthesize(request.text, config)

    if not audio_data:
        raise HTTPException(
            status_code=503,
            detail="TTS service unavailable"
        )

    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename={request.npc_id}_voice.mp3"
        }
    )


@router.post("/tts/stream")
async def stream_text_to_speech(
    request: TTSRequest,
    current_user: int = Depends(get_current_user_id),
):
    """
    流式文本转语音

    对长文本进行分段合成，流式返回音频
    """
    tts = get_tts_service()

    voice = VoiceType.XIAOYUN
    if request.voice:
        try:
            voice = VoiceType(request.voice)
        except ValueError:
            pass

    config = TTSConfig(voice=voice)

    async def generate():
        async for chunk in tts.synthesize_stream(request.text, config):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="audio/mpeg",
    )


# ==================== ASR Endpoints ====================

@router.post("/asr", response_model=APIResponse)
async def speech_to_text(
    request: ASRRequest,
    current_user: int = Depends(get_current_user_id),
):
    """
    语音识别 (Base64)

    将Base64编码的音频转换为文本
    """
    asr = get_asr_service()

    # 构建配置
    audio_format = ASRFormat.WAV
    if request.format:
        try:
            audio_format = ASRFormat(request.format)
        except ValueError:
            pass

    config = ASRConfig(
        format=audio_format,
        sample_rate=request.sample_rate or 16000,
    )

    # 识别
    result = await asr.recognize_base64(request.audio_base64, config)

    if not result:
        raise HTTPException(
            status_code=503,
            detail="ASR service unavailable or recognition failed"
        )

    return APIResponse(
        code=0,
        message="success",
        data=ASRResponse(
            text=result.text,
            confidence=result.confidence,
            duration=result.duration,
        ).model_dump()
    )


@router.post("/asr/upload", response_model=APIResponse)
async def speech_to_text_upload(
    file: UploadFile = File(..., description="音频文件"),
    format: str = Form("wav", description="音频格式"),
    sample_rate: int = Form(16000, description="采样率"),
    current_user: int = Depends(get_current_user_id),
):
    """
    语音识别 (文件上传)

    上传音频文件进行语音识别
    """
    # 读取文件
    audio_data = await file.read()

    if len(audio_data) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    # 限制文件大小 (10MB)
    if len(audio_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")

    asr = get_asr_service()

    # 构建配置
    audio_format = ASRFormat.WAV
    try:
        audio_format = ASRFormat(format)
    except ValueError:
        pass

    config = ASRConfig(
        format=audio_format,
        sample_rate=sample_rate,
    )

    # 根据文件大小选择识别方式
    if len(audio_data) > 1024 * 1024:  # 大于1MB使用文件转写
        result = await asr.recognize_file(audio_data, config)
    else:
        result = await asr.recognize(audio_data, config)

    if not result:
        raise HTTPException(
            status_code=503,
            detail="ASR service unavailable or recognition failed"
        )

    return APIResponse(
        code=0,
        message="success",
        data=ASRResponse(
            text=result.text,
            confidence=result.confidence,
            duration=result.duration,
        ).model_dump()
    )


# ==================== Voice Info Endpoints ====================

@router.get("/voices", response_model=APIResponse)
async def get_available_voices(
    current_user: int = Depends(get_current_user_id),
):
    """
    获取可用语音列表
    """
    voices = [
        VoiceInfo(id="xiaoyun", name="小云", gender="female", description="标准女声"),
        VoiceInfo(id="xiaogang", name="小刚", gender="male", description="标准男声"),
        VoiceInfo(id="ruoxi", name="若兮", gender="female", description="温柔女声"),
        VoiceInfo(id="siqi", name="思琪", gender="female", description="温柔女声"),
        VoiceInfo(id="sijia", name="思佳", gender="female", description="标准女声"),
        VoiceInfo(id="sicheng", name="思诚", gender="male", description="标准男声"),
        VoiceInfo(id="aiqi", name="艾琪", gender="female", description="温柔女声"),
        VoiceInfo(id="aijia", name="艾佳", gender="female", description="标准女声"),
        VoiceInfo(id="aicheng", name="艾诚", gender="male", description="标准男声"),
        VoiceInfo(id="aida", name="艾达", gender="male", description="标准男声"),
        VoiceInfo(id="ninger", name="宁儿", gender="female", description="甜美女声"),
        VoiceInfo(id="xiaobei", name="小北", gender="female", description="萝莉女声"),
        VoiceInfo(id="yina", name="伊娜", gender="female", description="浙普女声"),
        VoiceInfo(id="tingting", name="婷婷", gender="female", description="台普女声"),
        VoiceInfo(id="siyue", name="思悦", gender="female", description="温柔女声"),
        VoiceInfo(id="xiaomei", name="小美", gender="female", description="甜美女声"),
    ]

    return APIResponse(
        code=0,
        message="success",
        data=[v.model_dump() for v in voices]
    )


@router.get("/npc-voices", response_model=APIResponse)
async def get_npc_voices(
    current_user: int = Depends(get_current_user_id),
):
    """
    获取NPC语音映射
    """
    npc_voices = {
        "bei": {"voice_id": "xiaobei", "name": "小北", "description": "萝莉女声，适合活泼的小贝"},
        "aela": {"voice_id": "ruoxi", "name": "若兮", "description": "温柔女声，适合知性的艾拉"},
        "momo": {"voice_id": "ninger", "name": "宁儿", "description": "甜美女声，适合商人莫莫"},
        "chronos": {"voice_id": "sicheng", "name": "思诚", "description": "标准男声，适合守护者克洛诺斯"},
        "sesame": {"voice_id": "xiaobei", "name": "小北", "description": "萝莉女声，适合可爱的芝麻"},
    }

    return APIResponse(
        code=0,
        message="success",
        data=npc_voices
    )
