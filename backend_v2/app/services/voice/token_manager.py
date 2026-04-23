"""
MindPal Backend V2 - Aliyun Token Manager
阿里云 Token 管理器 - 自动获取和缓存 Token
"""

import json
import time
import hmac
import hashlib
import base64
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import httpx
from loguru import logger

from app.config import settings


class AliyunTokenManager:
    """
    阿里云 Token 管理器

    使用 AccessKey 自动获取 Token，并在过期前自动刷新
    """

    # Token API
    TOKEN_URL = "https://nls-meta.cn-shanghai.aliyuncs.com/"

    def __init__(self):
        self.access_key_id = settings.ALIYUN_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_ACCESS_KEY_SECRET
        self._token: Optional[str] = None
        self._token_expire_time: int = 0
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.access_key_id and self.access_key_secret)

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _sign(self, params: dict) -> str:
        """
        生成签名

        阿里云签名算法：
        1. 参数按字典序排序
        2. 拼接成 query string（URL 编码）
        3. 使用 HMAC-SHA1 签名
        4. Base64 编码
        """
        # 排序并 URL 编码
        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)

        # 构建待签名字符串
        string_to_sign = f"GET&%2F&{self._percent_encode(query_string)}"

        # HMAC-SHA1 签名
        key = f"{self.access_key_secret}&"
        signature = hmac.new(
            key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()

        return base64.b64encode(signature).decode('utf-8')

    def _percent_encode(self, s: str) -> str:
        """URL 编码（阿里云特殊处理）"""
        import urllib.parse
        res = urllib.parse.quote(s, safe='')
        res = res.replace('+', '%20')
        res = res.replace('*', '%2A')
        res = res.replace('%7E', '~')
        return res

    async def get_token(self) -> Optional[str]:
        """
        获取 Token

        如果 Token 有效，直接返回缓存的 Token
        如果 Token 过期或不存在，重新获取
        """
        if not self.is_configured:
            logger.warning("Aliyun AccessKey not configured")
            return None

        # 检查 Token 是否有效（提前 5 分钟刷新）
        current_time = int(time.time())
        if self._token and self._token_expire_time > current_time + 300:
            return self._token

        # 获取新 Token
        return await self._fetch_token()

    async def _fetch_token(self) -> Optional[str]:
        """从阿里云获取新 Token"""
        try:
            # 构建公共参数
            timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            nonce = str(uuid.uuid4())

            params = {
                'Action': 'CreateToken',
                'Version': '2019-02-28',
                'Format': 'JSON',
                'AccessKeyId': self.access_key_id,
                'SignatureMethod': 'HMAC-SHA1',
                'SignatureVersion': '1.0',
                'SignatureNonce': nonce,
                'Timestamp': timestamp,
                'RegionId': 'cn-shanghai',
            }

            # 签名
            params['Signature'] = self._sign(params)

            # 发送请求
            client = await self._get_client()
            response = await client.get(self.TOKEN_URL, params=params)

            if response.status_code == 200:
                result = response.json()

                if 'Token' in result:
                    token_info = result['Token']
                    self._token = token_info.get('Id')
                    self._token_expire_time = token_info.get('ExpireTime', 0)

                    logger.info(f"Aliyun Token obtained, expires at: {self._token_expire_time}")
                    return self._token
                else:
                    logger.error(f"Aliyun Token error: {result.get('Message', 'Unknown error')}")
                    return None
            else:
                logger.error(f"Aliyun Token request failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Aliyun Token fetch error: {e}")
            return None

    def invalidate(self):
        """使 Token 失效，强制下次重新获取"""
        self._token = None
        self._token_expire_time = 0


# 单例
_token_manager: Optional[AliyunTokenManager] = None


def get_token_manager() -> AliyunTokenManager:
    """获取 Token 管理器实例"""
    global _token_manager
    if _token_manager is None:
        _token_manager = AliyunTokenManager()
    return _token_manager
