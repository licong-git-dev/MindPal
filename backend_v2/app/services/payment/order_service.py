"""
MindPal Backend V2 - Order Service
订单服务
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.payment import (
    Order, OrderStatus, PaymentMethod, ProductType,
    PaymentLog, VIPSubscription, RechargeProduct
)
from app.models import Player


class OrderService:
    """订单服务"""

    ORDER_EXPIRE_MINUTES = 30  # 订单过期时间(分钟)

    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_order_no(self) -> str:
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex[:8].upper()
        return f"MP{timestamp}{random_str}"

    async def create_order(
        self,
        user_id: int,
        player_id: int,
        product_type: ProductType,
        product_id: str,
        product_name: str,
        amount: float,
        quantity: int = 1,
        remark: Optional[str] = None,
    ) -> Order:
        """
        创建订单

        Args:
            user_id: 用户ID
            player_id: 角色ID
            product_type: 商品类型
            product_id: 商品ID
            product_name: 商品名称
            amount: 金额
            quantity: 数量
            remark: 备注

        Returns:
            Order
        """
        order = Order(
            order_no=self._generate_order_no(),
            user_id=user_id,
            player_id=player_id,
            product_type=product_type,
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            amount=amount,
            status=OrderStatus.PENDING,
            expired_at=datetime.utcnow() + timedelta(minutes=self.ORDER_EXPIRE_MINUTES),
            remark=remark,
        )

        self.db.add(order)
        await self.db.flush()

        logger.info(f"Created order: {order.order_no}, amount: {amount}")
        return order

    async def get_order_by_no(self, order_no: str) -> Optional[Order]:
        """通过订单号获取订单"""
        stmt = select(Order).where(Order.order_no == order_no)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """通过ID获取订单"""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_orders(
        self,
        user_id: int,
        status: Optional[OrderStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Order]:
        """获取用户订单列表"""
        conditions = [Order.user_id == user_id]
        if status:
            conditions.append(Order.status == status)

        stmt = (
            select(Order)
            .where(and_(*conditions))
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_order_status(
        self,
        order: Order,
        status: OrderStatus,
        payment_method: Optional[PaymentMethod] = None,
        payment_no: Optional[str] = None,
    ) -> Order:
        """更新订单状态"""
        order.status = status
        order.updated_at = datetime.utcnow()

        if payment_method:
            order.payment_method = payment_method
        if payment_no:
            order.payment_no = payment_no
        if status == OrderStatus.PAID:
            order.paid_at = datetime.utcnow()

        await self.db.flush()
        return order

    async def mark_paid(
        self,
        order: Order,
        payment_method: PaymentMethod,
        payment_no: str,
    ) -> Order:
        """标记订单已支付"""
        return await self.update_order_status(
            order,
            OrderStatus.PAID,
            payment_method,
            payment_no,
        )

    async def deliver_order(self, order: Order) -> bool:
        """
        发货 (发放虚拟商品)

        Returns:
            是否成功
        """
        if order.status != OrderStatus.PAID:
            logger.warning(f"Order {order.order_no} is not paid, cannot deliver")
            return False

        try:
            # 获取角色
            stmt = select(Player).where(Player.id == order.player_id)
            result = await self.db.execute(stmt)
            player = result.scalar_one_or_none()

            if not player:
                logger.error(f"Player {order.player_id} not found")
                return False

            delivery_data = {}

            # 根据商品类型发货
            if order.product_type == ProductType.DIAMONDS:
                # 发放钻石
                product = await self._get_recharge_product(order.product_id)
                if product:
                    diamonds_to_add = (product.diamonds + product.bonus_diamonds) * order.quantity
                    player.diamonds = (player.diamonds or 0) + diamonds_to_add
                    delivery_data["diamonds_added"] = diamonds_to_add

            elif order.product_type == ProductType.VIP:
                # 开通VIP
                product = await self._get_recharge_product(order.product_id)
                if product and product.vip_days > 0:
                    await self._activate_vip(order, player, product.vip_days)
                    delivery_data["vip_days"] = product.vip_days

            elif order.product_type == ProductType.ENERGY:
                # 发放体力
                product = await self._get_recharge_product(order.product_id)
                if product:
                    # 假设items字段包含体力数量
                    items = json.loads(product.items or '{}')
                    energy = items.get('energy', 0)
                    player.energy = min((player.energy or 0) + energy, 200)
                    delivery_data["energy_added"] = energy

            elif order.product_type == ProductType.ITEM_PACK:
                # 发放礼包物品
                product = await self._get_recharge_product(order.product_id)
                if product:
                    items = json.loads(product.items or '[]')
                    # TODO: 添加物品到背包
                    delivery_data["items"] = items

            # 更新订单状态
            order.status = OrderStatus.DELIVERED
            order.delivered_at = datetime.utcnow()
            order.delivery_data = json.dumps(delivery_data)

            await self.db.flush()

            logger.info(f"Order {order.order_no} delivered: {delivery_data}")
            return True

        except Exception as e:
            logger.error(f"Failed to deliver order {order.order_no}: {e}")
            return False

    async def _get_recharge_product(self, product_id: str) -> Optional[RechargeProduct]:
        """获取充值商品"""
        stmt = select(RechargeProduct).where(RechargeProduct.product_id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _activate_vip(self, order: Order, player: Player, days: int):
        """激活VIP"""
        now = datetime.utcnow()

        # 查找现有订阅
        stmt = select(VIPSubscription).where(
            and_(
                VIPSubscription.player_id == player.id,
                VIPSubscription.is_active == 1
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing and existing.expired_at > now:
            # 续期
            existing.expired_at = existing.expired_at + timedelta(days=days)
            existing.updated_at = now
        else:
            # 新订阅
            subscription = VIPSubscription(
                user_id=order.user_id,
                player_id=player.id,
                vip_level=1,
                started_at=now,
                expired_at=now + timedelta(days=days),
                order_id=order.id,
                is_active=1,
            )
            self.db.add(subscription)

    async def cancel_order(self, order: Order) -> bool:
        """取消订单"""
        if order.status not in [OrderStatus.PENDING]:
            return False

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def log_payment(
        self,
        order: Order,
        payment_method: PaymentMethod,
        action: str,
        request_data: Optional[str] = None,
        response_data: Optional[str] = None,
        success: bool = False,
        error_msg: Optional[str] = None,
    ):
        """记录支付日志"""
        log = PaymentLog(
            order_id=order.id,
            order_no=order.order_no,
            payment_method=payment_method,
            action=action,
            request_data=request_data,
            response_data=response_data,
            success=1 if success else 0,
            error_msg=error_msg,
        )
        self.db.add(log)
        await self.db.flush()

    async def get_recharge_products(
        self,
        product_type: Optional[ProductType] = None,
    ) -> List[RechargeProduct]:
        """获取充值商品列表"""
        conditions = [RechargeProduct.is_active == 1]
        if product_type:
            conditions.append(RechargeProduct.product_type == product_type)

        stmt = (
            select(RechargeProduct)
            .where(and_(*conditions))
            .order_by(RechargeProduct.sort_order, RechargeProduct.price)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


def get_order_service(db: AsyncSession) -> OrderService:
    """获取订单服务实例"""
    return OrderService(db)
