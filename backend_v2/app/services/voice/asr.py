"""
MindPal Backend V2 - ASR (Automatic Speech Recognition) Service
阿里云语音识别服务
"""

import base64
from typing import Optional, Dict, Any, List
from enum import Enum

import httpx
from loguru import logger

from app.config import settings
from app.services.voice.token_manager import get_token_manager


class ASRFormat(str, Enum):
    """音频格式"""
    PCM = "pcm"
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    OPUS = "opus"
    SPEEX = "speex"
    AAC = "aac"


class ASRResult:
    """ASR识别结果"""
    def __init__(
        self,
        text: str,
        confidence: float = 1.0,
        duration: float = 0.0,
        words: Optional[List[Dict]] = None,
    ):
        self.text = text
        self.confidence = confidence
        self.duration = duration
        self.words = words or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "duration": self.duration,
            "words": self.words,
        }


class ASRConfig:
    """ASR配置"""
    def __init__(
        self,
        format: ASRFormat = ASRFormat.WAV,
        sample_rate: int = 16000,
        enable_punctuation: bool = True,
        enable_inverse_text: bool = False,
        enable_voice_detection: bool = True,
    ):
        self.format = format
        self.sample_rate = sample_rate
        self.enable_punctuation = enable_punctuation
        self.enable_inverse_text = enable_inverse_text
        self.enable_voice_detection = enable_voice_detection


class ASRService:
    """阿里云ASR服务"""

    # 阿里云一句话识别API端点
    API_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr"

    # 文件识别API (用于长音频)
    FILE_API_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/FlashRecognizer"

    def __init__(self):
        self.app_key = getattr(settings, 'ALIYUN_ASR_APP_KEY', None)
        self.token_manager = get_token_manager()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _get_token(self) -> Optional[str]:
        """获取访问令牌"""
        return await self.token_manager.get_token()

    async def recognize(
        self,
        audio_data: bytes,
        config: Optional[ASRConfig] = None,
    ) -> Optional[ASRResult]:
        """
        语音识别 (一句话识别，适合60秒以内的音频)

        Args:
            audio_data: 音频数据
            config: ASR配置

        Returns:
            ASRResult或None
        """
        # 获取 Token
        access_token = await self._get_token()

        if not self.app_key or not access_token:
            logger.warning("ASR credentials not configured")
            return None

        if not audio_data:
            return None

        config = config or ASRConfig()

        # 构建请求URL
        params = {
            "appkey": self.app_key,
            "format": config.format.value,
            "sample_rate": config.sample_rate,
            "enable_punctuation_prediction": str(config.enable_punctuation).lower(),
            "enable_inverse_text_normalization": str(config.enable_inverse_text).lower(),
            "enable_voice_detection": str(config.enable_voice_detection).lower(),
        }

        url = f"{self.API_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])

        try:
            client = await self._get_client()
            response = await client.post(
                url,
                content=audio_data,
                headers={
                    "Content-Type": f"application/octet-stream",
                    "X-NLS-Token": access_token,
                }
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == 20000000:
                    return ASRResult(
                        text=result.get("result", ""),
                        confidence=result.get("confidence", 1.0),
                        duration=result.get("duration", 0.0),
                    )
                else:
                    logger.error(f"ASR error: {result.get('message')}")
                    return None
            else:
                logger.error(f"ASR request failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"ASR recognition error: {e}")
            return None

    async def recognize_file(
        self,
        audio_data: bytes,
        config: Optional[ASRConfig] = None,
    ) -> Optional[ASRResult]:
        """
        文件转写 (适合长音频，使用Flash识别)

        Args:
            audio_data: 音频数据
            config: ASR配置

        Returns:
            ASRResult或None
        """
        # 获取 Token
        access_token = await self._get_token()

        if not self.app_key or not access_token:
            logger.warning("ASR credentials not configured")
            return None

        config = config or ASRConfig()

        # 构建请求参数
        params = {
            "appkey": self.app_key,
            "format": config.format.value,
            "sample_rate": config.sample_rate,
        }

        url = f"{self.FILE_API_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])

        try:
            client = await self._get_client()
            response = await client.post(
                url,
                content=audio_data,
                headers={
                    "Content-Type": "application/octet-stream",
                    "X-NLS-Token": access_token,
                }
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == 20000000:
                    # Flash识别返回多个句子
                    sentences = result.get("flash_result", {}).get("sentences", [])
                    full_text = "".join([s.get("text", "") for s in sentences])
                    return ASRResult(
                        text=full_text,
                        confidence=1.0,
                        duration=result.get("flash_result", {}).get("duration", 0.0),
                        words=[{"text": s.get("text"), "begin": s.get("begin_time"), "end": s.get("end_time")}
                               for s in sentences]
                    )
                else:
                    logger.error(f"ASR file error: {result.get('message')}")
                    return None
            else:
                logger.error(f"ASR file request failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"ASR file recognition error: {e}")
            return None

    async def recognize_base64(
        self,
        audio_base64: str,
        config: Optional[ASRConfig] = None,
    ) -> Optional[ASRResult]:
        """
        识别Base64编码的音频

        Args:
            audio_base64: Base64编码的音频数据
            config: ASR配置

        Returns:
            ASRResult或None
        """
        try:
            audio_data = base64.b64decode(audio_base64)
            return await self.recognize(audio_data, config)
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")
            return None


# 单例
_asr_service: Optional[ASRService] = None


def get_asr_service() -> ASRService:
    """获取ASR服务实例"""
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service
