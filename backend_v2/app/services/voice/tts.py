"""
MindPal Backend V2 - TTS (Text-to-Speech) Service
阿里云语音合成服务
"""

import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from enum import Enum

import httpx
from loguru import logger

from app.config import settings
from app.services.voice.token_manager import get_token_manager


class VoiceType(str, Enum):
    """语音类型"""
    # 通用场景
    XIAOYUN = "xiaoyun"      # 标准女声
    XIAOGANG = "xiaogang"    # 标准男声
    RUOXI = "ruoxi"          # 温柔女声
    SIQI = "siqi"            # 温柔女声
    SIJIA = "sijia"          # 标准女声
    SICHENG = "sicheng"      # 标准男声
    AIQI = "aiqi"            # 温柔女声
    AIJIA = "aijia"          # 标准女声
    AICHENG = "aicheng"      # 标准男声
    AIDA = "aida"            # 标准男声

    # 情感场景
    NINGER = "ninger"        # 甜美女声
    XIAOBEI = "xiaobei"      # 萝莉女声 (适合小贝)
    YINA = "yina"            # 浙普女声
    TINGTING = "tingting"    # 台普女声

    # 客服场景
    SIYUE = "siyue"          # 温柔女声
    SIYUAN = "siyuan"        # 男声
    XIAOMEI = "xiaomei"      # 甜美女声


class TTSConfig:
    """TTS配置"""
    def __init__(
        self,
        voice: VoiceType = VoiceType.XIAOBEI,
        format: str = "mp3",
        sample_rate: int = 16000,
        volume: int = 50,
        speech_rate: int = 0,
        pitch_rate: int = 0,
    ):
        self.voice = voice
        self.format = format  # mp3, wav, pcm
        self.sample_rate = sample_rate  # 8000, 16000, 24000
        self.volume = volume  # 0-100
        self.speech_rate = speech_rate  # -500 to 500
        self.pitch_rate = pitch_rate  # -500 to 500


class TTSService:
    """阿里云TTS服务"""

    # 阿里云TTS API端点
    API_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts"

    def __init__(self):
        self.app_key = getattr(settings, 'ALIYUN_TTS_APP_KEY', None)
        self.token_manager = get_token_manager()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def synthesize(
        self,
        text: str,
        config: Optional[TTSConfig] = None,
    ) -> Optional[bytes]:
        """
        文本转语音

        Args:
            text: 要合成的文本
            config: TTS配置

        Returns:
            音频数据(bytes)或None
        """
        # 获取 Token
        access_token = await self.token_manager.get_token()

        if not self.app_key or not access_token:
            logger.warning("TTS credentials not configured")
            return None

        if not text or len(text.strip()) == 0:
            return None

        config = config or TTSConfig()

        # 构建请求参数
        params = {
            "appkey": self.app_key,
            "token": access_token,
            "text": text,
            "format": config.format,
            "sample_rate": config.sample_rate,
            "voice": config.voice.value,
            "volume": config.volume,
            "speech_rate": config.speech_rate,
            "pitch_rate": config.pitch_rate,
        }

        try:
            client = await self._get_client()
            response = await client.post(
                self.API_URL,
                data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "audio" in content_type:
                    return response.content
                else:
                    # 可能是错误响应
                    error = response.json()
                    logger.error(f"TTS error: {error}")
                    return None
            else:
                logger.error(f"TTS request failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None

    async def synthesize_stream(
        self,
        text: str,
        config: Optional[TTSConfig] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        流式文本转语音

        Args:
            text: 要合成的文本
            config: TTS配置

        Yields:
            音频数据块
        """
        # 对于长文本，分段合成
        max_length = 300  # 每段最大字符数

        if len(text) <= max_length:
            audio = await self.synthesize(text, config)
            if audio:
                yield audio
            return

        # 按句子分割
        sentences = self._split_text(text, max_length)

        for sentence in sentences:
            if sentence.strip():
                audio = await self.synthesize(sentence.strip(), config)
                if audio:
                    yield audio
                    # 短暂延迟，避免请求过快
                    await asyncio.sleep(0.1)

    def _split_text(self, text: str, max_length: int) -> list:
        """
        智能分割文本

        优先按标点符号分割，保持语句完整性
        """
        # 分割符优先级
        delimiters = ['。', '！', '？', '；', '，', '、', '.', '!', '?', ';', ',']

        result = []
        current = ""

        for char in text:
            current += char

            if len(current) >= max_length:
                # 尝试在最近的分隔符处分割
                split_pos = -1
                for delim in delimiters:
                    pos = current.rfind(delim)
                    if pos > 0:
                        split_pos = pos + 1
                        break

                if split_pos > 0:
                    result.append(current[:split_pos])
                    current = current[split_pos:]
                else:
                    # 没有找到分隔符，强制分割
                    result.append(current)
                    current = ""

        if current:
            result.append(current)

        return result

    def get_voice_for_npc(self, npc_id: str) -> VoiceType:
        """
        获取NPC对应的语音类型

        Args:
            npc_id: NPC ID

        Returns:
            VoiceType
        """
        voice_mapping = {
            "bei": VoiceType.XIAOBEI,      # 小贝 - 萝莉女声
            "aela": VoiceType.RUOXI,       # 艾拉 - 温柔女声
            "momo": VoiceType.NINGER,      # 莫莫 - 甜美女声
            "chronos": VoiceType.SICHENG,  # 克洛诺斯 - 标准男声
            "sesame": VoiceType.XIAOBEI,   # 芝麻 - 萝莉女声
        }
        return voice_mapping.get(npc_id, VoiceType.XIAOYUN)


# 单例
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """获取TTS服务实例"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
