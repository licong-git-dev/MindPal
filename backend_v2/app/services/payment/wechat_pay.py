"""
MindPal Backend V2 - WeChat Pay Service
微信支付服务
"""

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from xml.etree import ElementTree

import httpx
from loguru import logger

from app.config import settings


class WechatPayConfig:
    """微信支付配置"""
    def __init__(self):
        self.app_id = getattr(settings, 'WECHAT_APP_ID', None)
        self.mch_id = getattr(settings, 'WECHAT_MCH_ID', None)  # 商户号
        self.api_key = getattr(settings, 'WECHAT_API_KEY', None)  # API密钥
        self.api_v3_key = getattr(settings, 'WECHAT_API_V3_KEY', None)  # APIv3密钥
        self.serial_no = getattr(settings, 'WECHAT_SERIAL_NO', None)  # 证书序列号
        self.private_key = getattr(settings, 'WECHAT_PRIVATE_KEY', None)  # 私钥
        self.notify_url = getattr(settings, 'WECHAT_NOTIFY_URL', None)  # 回调地址

    @property
    def is_configured(self) -> bool:
        return all([self.app_id, self.mch_id, self.api_key])


class WechatPayService:
    """微信支付服务"""

    # 统一下单API (V2)
    UNIFIED_ORDER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"

    # 订单查询API
    ORDER_QUERY_URL = "https://api.mch.weixin.qq.com/pay/orderquery"

    # 关闭订单API
    CLOSE_ORDER_URL = "https://api.mch.weixin.qq.com/pay/closeorder"

    # 退款API
    REFUND_URL = "https://api.mch.weixin.qq.com/secapi/pay/refund"

    def __init__(self):
        self.config = WechatPayConfig()
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

    def _generate_nonce_str(self) -> str:
        """生成随机字符串"""
        return uuid.uuid4().hex[:32]

    def _sign(self, data: Dict[str, Any]) -> str:
        """
        签名 (MD5)

        Args:
            data: 待签名数据

        Returns:
            签名字符串
        """
        # 按字典序排序
        sorted_data = sorted([(k, v) for k, v in data.items() if v])
        string_a = "&".join([f"{k}={v}" for k, v in sorted_data])
        string_sign_temp = f"{string_a}&key={self.config.api_key}"

        # MD5签名
        sign = hashlib.md5(string_sign_temp.encode('utf-8')).hexdigest().upper()
        return sign

    def _dict_to_xml(self, data: Dict[str, Any]) -> str:
        """字典转XML"""
        xml = ["<xml>"]
        for key, value in data.items():
            if isinstance(value, str):
                xml.append(f"<{key}><![CDATA[{value}]]></{key}>")
            else:
                xml.append(f"<{key}>{value}</{key}>")
        xml.append("</xml>")
        return "".join(xml)

    def _xml_to_dict(self, xml_str: str) -> Dict[str, str]:
        """XML转字典"""
        root = ElementTree.fromstring(xml_str)
        return {child.tag: child.text or "" for child in root}

    async def create_unified_order(
        self,
        order_no: str,
        amount: float,
        description: str,
        trade_type: str = "NATIVE",  # JSAPI, NATIVE, APP, MWEB
        openid: Optional[str] = None,
        client_ip: str = "127.0.0.1",
    ) -> Optional[Dict[str, Any]]:
        """
        统一下单

        Args:
            order_no: 商户订单号
            amount: 金额(元)
            description: 商品描述
            trade_type: 交易类型
            openid: 用户openid (JSAPI必须)
            client_ip: 客户端IP

        Returns:
            支付参数或None
        """
        if not self.config.is_configured:
            logger.warning("WeChat Pay not configured")
            return None

        # 构建请求参数
        params = {
            "appid": self.config.app_id,
            "mch_id": self.config.mch_id,
            "nonce_str": self._generate_nonce_str(),
            "body": description[:128],  # 商品描述限128字符
            "out_trade_no": order_no,
            "total_fee": int(amount * 100),  # 转为分
            "spbill_create_ip": client_ip,
            "notify_url": self.config.notify_url,
            "trade_type": trade_type,
        }

        if trade_type == "JSAPI" and openid:
            params["openid"] = openid

        # 签名
        params["sign"] = self._sign(params)

        # 转XML
        xml_data = self._dict_to_xml(params)

        try:
            client = await self._get_client()
            response = await client.post(
                self.UNIFIED_ORDER_URL,
                content=xml_data,
                headers={"Content-Type": "application/xml"}
            )

            result = self._xml_to_dict(response.text)

            if result.get("return_code") == "SUCCESS" and result.get("result_code") == "SUCCESS":
                # 返回支付参数
                if trade_type == "NATIVE":
                    return {
                        "prepay_id": result.get("prepay_id"),
                        "code_url": result.get("code_url"),  # 二维码链接
                    }
                elif trade_type == "JSAPI":
                    # 生成JSAPI支付参数
                    timestamp = str(int(time.time()))
                    nonce_str = self._generate_nonce_str()
                    package = f"prepay_id={result.get('prepay_id')}"

                    pay_params = {
                        "appId": self.config.app_id,
                        "timeStamp": timestamp,
                        "nonceStr": nonce_str,
                        "package": package,
                        "signType": "MD5",
                    }
                    pay_params["paySign"] = self._sign(pay_params)
                    return pay_params
                elif trade_type == "APP":
                    # 生成APP支付参数
                    timestamp = str(int(time.time()))
                    nonce_str = self._generate_nonce_str()

                    pay_params = {
                        "appid": self.config.app_id,
                        "partnerid": self.config.mch_id,
                        "prepayid": result.get("prepay_id"),
                        "package": "Sign=WXPay",
                        "noncestr": nonce_str,
                        "timestamp": timestamp,
                    }
                    pay_params["sign"] = self._sign(pay_params)
                    return pay_params
                else:
                    return result
            else:
                logger.error(f"WeChat Pay error: {result.get('return_msg')} - {result.get('err_code_des')}")
                return None

        except Exception as e:
            logger.error(f"WeChat Pay create order error: {e}")
            return None

    async def query_order(
        self,
        order_no: Optional[str] = None,
        transaction_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        查询订单

        Args:
            order_no: 商户订单号
            transaction_id: 微信支付订单号

        Returns:
            订单信息或None
        """
        if not self.config.is_configured:
            return None

        params = {
            "appid": self.config.app_id,
            "mch_id": self.config.mch_id,
            "nonce_str": self._generate_nonce_str(),
        }

        if transaction_id:
            params["transaction_id"] = transaction_id
        elif order_no:
            params["out_trade_no"] = order_no
        else:
            return None

        params["sign"] = self._sign(params)
        xml_data = self._dict_to_xml(params)

        try:
            client = await self._get_client()
            response = await client.post(
                self.ORDER_QUERY_URL,
                content=xml_data,
                headers={"Content-Type": "application/xml"}
            )

            result = self._xml_to_dict(response.text)

            if result.get("return_code") == "SUCCESS":
                return result
            else:
                logger.error(f"WeChat Pay query error: {result.get('return_msg')}")
                return None

        except Exception as e:
            logger.error(f"WeChat Pay query order error: {e}")
            return None

    def verify_notify(self, xml_data: str) -> Optional[Dict[str, Any]]:
        """
        验证支付回调

        Args:
            xml_data: 回调XML数据

        Returns:
            验证后的数据或None
        """
        try:
            data = self._xml_to_dict(xml_data)

            if data.get("return_code") != "SUCCESS":
                return None

            # 验证签名
            sign = data.pop("sign", "")
            calculated_sign = self._sign(data)

            if sign != calculated_sign:
                logger.warning("WeChat Pay notify signature mismatch")
                return None

            return data

        except Exception as e:
            logger.error(f"WeChat Pay verify notify error: {e}")
            return None

    def generate_notify_response(self, success: bool) -> str:
        """生成回调响应"""
        if success:
            return self._dict_to_xml({
                "return_code": "SUCCESS",
                "return_msg": "OK"
            })
        else:
            return self._dict_to_xml({
                "return_code": "FAIL",
                "return_msg": "FAIL"
            })


# 单例
_wechat_pay_service: Optional[WechatPayService] = None


def get_wechat_pay_service() -> WechatPayService:
    """获取微信支付服务实例"""
    global _wechat_pay_service
    if _wechat_pay_service is None:
        _wechat_pay_service = WechatPayService()
    return _wechat_pay_service
