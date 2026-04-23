"""
MindPal Backend V2 - Mock Payment Service
模拟支付服务 (开发测试用)
"""

import asyncio
import random
import string
from datetime import datetime
from typing import Optional, Dict, Any

from loguru import logger


class MockPaymentService:
    """
    模拟支付服务

    用于开发测试阶段，模拟微信/支付宝支付流程
    """

    def __init__(self):
        self._pending_orders: Dict[str, Dict] = {}

    def _generate_trade_no(self) -> str:
        """生成模拟交易号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.digits, k=10))
        return f"MOCK{timestamp}{random_str}"

    async def create_payment(
        self,
        order_no: str,
        amount: float,
        description: str,
        payment_method: str = "mock",
    ) -> Dict[str, Any]:
        """
        创建模拟支付

        Args:
            order_no: 订单号
            amount: 金额
            description: 描述
            payment_method: 支付方式

        Returns:
            支付信息
        """
        trade_no = self._generate_trade_no()

        # 保存待支付订单
        self._pending_orders[order_no] = {
            "trade_no": trade_no,
            "amount": amount,
            "description": description,
            "payment_method": payment_method,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending",
        }

        logger.info(f"[MockPay] Created payment: {order_no} -> {trade_no}, amount: {amount}")

        return {
            "success": True,
            "order_no": order_no,
            "trade_no": trade_no,
            "amount": amount,
            "payment_method": payment_method,
            # 模拟支付链接/二维码
            "pay_url": f"http://localhost:8000/api/v1/payment/mock/pay/{order_no}",
            "qr_code": f"MOCK_QR_{order_no}",
            "message": "模拟支付已创建，访问 pay_url 完成支付",
        }

    async def confirm_payment(self, order_no: str) -> Dict[str, Any]:
        """
        确认支付（模拟用户完成支付）

        Args:
            order_no: 订单号

        Returns:
            支付结果
        """
        if order_no not in self._pending_orders:
            return {
                "success": False,
                "message": "订单不存在或已处理",
            }

        order_info = self._pending_orders[order_no]

        # 模拟支付延迟
        await asyncio.sleep(0.5)

        # 更新状态
        order_info["status"] = "paid"
        order_info["paid_at"] = datetime.utcnow().isoformat()

        logger.info(f"[MockPay] Payment confirmed: {order_no}")

        return {
            "success": True,
            "order_no": order_no,
            "trade_no": order_info["trade_no"],
            "amount": order_info["amount"],
            "paid_at": order_info["paid_at"],
            "message": "模拟支付成功",
        }

    async def query_payment(self, order_no: str) -> Dict[str, Any]:
        """
        查询支付状态

        Args:
            order_no: 订单号

        Returns:
            支付状态
        """
        if order_no not in self._pending_orders:
            return {
                "success": False,
                "status": "not_found",
                "message": "订单不存在",
            }

        order_info = self._pending_orders[order_no]

        return {
            "success": True,
            "order_no": order_no,
            "trade_no": order_info["trade_no"],
            "amount": order_info["amount"],
            "status": order_info["status"],
            "created_at": order_info["created_at"],
            "paid_at": order_info.get("paid_at"),
        }

    async def cancel_payment(self, order_no: str) -> Dict[str, Any]:
        """
        取消支付

        Args:
            order_no: 订单号

        Returns:
            取消结果
        """
        if order_no in self._pending_orders:
            del self._pending_orders[order_no]
            logger.info(f"[MockPay] Payment cancelled: {order_no}")
            return {
                "success": True,
                "message": "支付已取消",
            }
        return {
            "success": False,
            "message": "订单不存在",
        }


# 单例
_mock_payment_service: Optional[MockPaymentService] = None


def get_mock_payment_service() -> MockPaymentService:
    """获取模拟支付服务实例"""
    global _mock_payment_service
    if _mock_payment_service is None:
        _mock_payment_service = MockPaymentService()
    return _mock_payment_service
