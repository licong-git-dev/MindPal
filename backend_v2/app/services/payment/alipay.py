"""
MindPal Backend V2 - Alipay Service
支付宝支付服务
"""

import base64
import hashlib
import json
import time
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any

import httpx
from loguru import logger

from app.config import settings


class AlipayConfig:
    """支付宝配置"""
    def __init__(self):
        self.app_id = getattr(settings, 'ALIPAY_APP_ID', None)
        self.private_key = getattr(settings, 'ALIPAY_PRIVATE_KEY', None)
        self.public_key = getattr(settings, 'ALIPAY_PUBLIC_KEY', None)
        self.alipay_public_key = getattr(settings, 'ALIPAY_ALIPAY_PUBLIC_KEY', None)
        self.notify_url = getattr(settings, 'ALIPAY_NOTIFY_URL', None)
        self.return_url = getattr(settings, 'ALIPAY_RETURN_URL', None)
        self.gateway = "https://openapi.alipay.com/gateway.do"
        self.sandbox_gateway = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
        self.use_sandbox = getattr(settings, 'ALIPAY_SANDBOX', True)

    @property
    def is_configured(self) -> bool:
        return all([self.app_id, self.private_key])

    @property
    def api_gateway(self) -> str:
        return self.sandbox_gateway if self.use_sandbox else self.gateway


class AlipayService:
    """支付宝支付服务"""

    def __init__(self):
        self.config = AlipayConfig()
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

    def _sign_rsa2(self, content: str) -> str:
        """
        RSA2签名

        Args:
            content: 待签名内容

        Returns:
            签名字符串
        """
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend

            # 加载私钥
            private_key_pem = f"-----BEGIN RSA PRIVATE KEY-----\n{self.config.private_key}\n-----END RSA PRIVATE KEY-----"
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )

            # 签名
            signature = private_key.sign(
                content.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            return base64.b64encode(signature).decode('utf-8')
        except ImportError:
            logger.error("cryptography library required for RSA signing")
            return ""
        except Exception as e:
            logger.error(f"RSA sign error: {e}")
            return ""

    def _verify_rsa2(self, content: str, signature: str) -> bool:
        """
        验证RSA2签名

        Args:
            content: 原始内容
            signature: 签名

        Returns:
            是否验证通过
        """
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend

            # 加载支付宝公钥
            public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{self.config.alipay_public_key}\n-----END PUBLIC KEY-----"
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )

            # 验签
            public_key.verify(
                base64.b64decode(signature),
                content.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except ImportError:
            logger.error("cryptography library required for RSA verification")
            return False
        except Exception as e:
            logger.error(f"RSA verify error: {e}")
            return False

    def _build_sign_content(self, params: Dict[str, Any]) -> str:
        """构建待签名字符串"""
        sorted_params = sorted([(k, v) for k, v in params.items() if v and k != 'sign'])
        return "&".join([f"{k}={v}" for k, v in sorted_params])

    async def create_trade(
        self,
        order_no: str,
        amount: float,
        subject: str,
        body: Optional[str] = None,
        timeout_express: str = "30m",
        product_code: str = "FAST_INSTANT_TRADE_PAY",
    ) -> Optional[str]:
        """
        创建交易 (网页支付)

        Args:
            order_no: 商户订单号
            amount: 金额(元)
            subject: 商品标题
            body: 商品描述
            timeout_express: 超时时间
            product_code: 产品码

        Returns:
            支付链接或None
        """
        if not self.config.is_configured:
            logger.warning("Alipay not configured")
            return None

        # 业务参数
        biz_content = {
            "out_trade_no": order_no,
            "total_amount": f"{amount:.2f}",
            "subject": subject[:256],
            "product_code": product_code,
            "timeout_express": timeout_express,
        }
        if body:
            biz_content["body"] = body[:128]

        # 公共参数
        params = {
            "app_id": self.config.app_id,
            "method": "alipay.trade.page.pay",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps(biz_content),
        }

        if self.config.notify_url:
            params["notify_url"] = self.config.notify_url
        if self.config.return_url:
            params["return_url"] = self.config.return_url

        # 签名
        sign_content = self._build_sign_content(params)
        params["sign"] = self._sign_rsa2(sign_content)

        if not params["sign"]:
            return None

        # 构建支付URL
        query_string = urllib.parse.urlencode(params)
        pay_url = f"{self.config.api_gateway}?{query_string}"

        return pay_url

    async def create_app_trade(
        self,
        order_no: str,
        amount: float,
        subject: str,
        body: Optional[str] = None,
        timeout_express: str = "30m",
    ) -> Optional[str]:
        """
        创建APP支付订单

        Args:
            order_no: 商户订单号
            amount: 金额(元)
            subject: 商品标题
            body: 商品描述
            timeout_express: 超时时间

        Returns:
            订单信息字符串 (用于客户端调起支付)
        """
        if not self.config.is_configured:
            logger.warning("Alipay not configured")
            return None

        # 业务参数
        biz_content = {
            "out_trade_no": order_no,
            "total_amount": f"{amount:.2f}",
            "subject": subject[:256],
            "product_code": "QUICK_MSECURITY_PAY",
            "timeout_express": timeout_express,
        }
        if body:
            biz_content["body"] = body[:128]

        # 公共参数
        params = {
            "app_id": self.config.app_id,
            "method": "alipay.trade.app.pay",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps(biz_content),
        }

        if self.config.notify_url:
            params["notify_url"] = self.config.notify_url

        # 签名
        sign_content = self._build_sign_content(params)
        params["sign"] = self._sign_rsa2(sign_content)

        if not params["sign"]:
            return None

        # 返回订单字符串
        return urllib.parse.urlencode(params)

    async def query_trade(self, order_no: str) -> Optional[Dict[str, Any]]:
        """
        查询交易

        Args:
            order_no: 商户订单号

        Returns:
            交易信息或None
        """
        if not self.config.is_configured:
            return None

        # 业务参数
        biz_content = {
            "out_trade_no": order_no,
        }

        # 公共参数
        params = {
            "app_id": self.config.app_id,
            "method": "alipay.trade.query",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps(biz_content),
        }

        # 签名
        sign_content = self._build_sign_content(params)
        params["sign"] = self._sign_rsa2(sign_content)

        try:
            client = await self._get_client()
            response = await client.post(
                self.config.api_gateway,
                data=params,
            )

            result = response.json()
            trade_response = result.get("alipay_trade_query_response", {})

            if trade_response.get("code") == "10000":
                return trade_response
            else:
                logger.error(f"Alipay query error: {trade_response.get('sub_msg')}")
                return None

        except Exception as e:
            logger.error(f"Alipay query trade error: {e}")
            return None

    def verify_notify(self, params: Dict[str, str]) -> bool:
        """
        验证异步通知

        Args:
            params: 通知参数

        Returns:
            是否验证通过
        """
        if not params:
            return False

        # 获取签名
        sign = params.pop("sign", "")
        sign_type = params.pop("sign_type", "RSA2")

        if sign_type != "RSA2":
            logger.warning(f"Unsupported sign type: {sign_type}")
            return False

        # 构建待验签字符串
        sign_content = self._build_sign_content(params)

        # 验签
        return self._verify_rsa2(sign_content, sign)

    def get_notify_response(self, success: bool) -> str:
        """生成通知响应"""
        return "success" if success else "fail"


# 单例
_alipay_service: Optional[AlipayService] = None


def get_alipay_service() -> AlipayService:
    """获取支付宝服务实例"""
    global _alipay_service
    if _alipay_service is None:
        _alipay_service = AlipayService()
    return _alipay_service
