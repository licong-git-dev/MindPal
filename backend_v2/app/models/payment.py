"""
MindPal Backend V2 - Payment Models
支付系统数据模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PaymentMethod(str, enum.Enum):
    """支付方式"""
    WECHAT = "wechat"
    ALIPAY = "alipay"


class OrderStatus(str, enum.Enum):
    """订单状态"""
    PENDING = "pending"        # 待支付
    PAID = "paid"              # 已支付
    DELIVERED = "delivered"    # 已发货(虚拟商品已发放)
    CANCELLED = "cancelled"    # 已取消
    REFUNDED = "refunded"      # 已退款
    FAILED = "failed"          # 支付失败


class ProductType(str, enum.Enum):
    """商品类型"""
    DIAMONDS = "diamonds"      # 钻石充值
    VIP = "vip"                # VIP会员
    ITEM_PACK = "item_pack"    # 礼包
    ENERGY = "energy"          # 体力


class Order(Base):
    """订单表"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False, index=True)  # 订单号
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # 商品信息
    product_type = Column(SQLEnum(ProductType), nullable=False)
    product_id = Column(String(64), nullable=True)  # 具体商品ID
    product_name = Column(String(128), nullable=False)
    quantity = Column(Integer, default=1)

    # 金额
    amount = Column(Float, nullable=False)  # 订单金额(元)
    currency = Column(String(10), default="CNY")

    # 支付信息
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
    payment_no = Column(String(128), nullable=True)  # 第三方支付流水号
    paid_at = Column(DateTime, nullable=True)

    # 状态
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)

    # 发货信息
    delivered_at = Column(DateTime, nullable=True)
    delivery_data = Column(Text, nullable=True)  # JSON格式的发货数据

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expired_at = Column(DateTime, nullable=True)  # 订单过期时间

    # 备注
    remark = Column(Text, nullable=True)

    # 关系
    user = relationship("User", backref="orders")
    player = relationship("Player", backref="orders")


class PaymentLog(Base):
    """支付日志表"""
    __tablename__ = "payment_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    order_no = Column(String(64), nullable=False)

    # 支付方式
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)

    # 请求/响应
    action = Column(String(32), nullable=False)  # create, query, notify, refund
    request_data = Column(Text, nullable=True)
    response_data = Column(Text, nullable=True)

    # 状态
    success = Column(Integer, default=0)  # 0失败 1成功
    error_msg = Column(Text, nullable=True)

    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    order = relationship("Order", backref="payment_logs")


class VIPSubscription(Base):
    """VIP订阅表"""
    __tablename__ = "vip_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # VIP等级
    vip_level = Column(Integer, default=1)  # 1=月卡, 2=季卡, 3=年卡

    # 订阅时间
    started_at = Column(DateTime, nullable=False)
    expired_at = Column(DateTime, nullable=False)

    # 关联订单
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    # 状态
    is_active = Column(Integer, default=1)
    auto_renew = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", backref="vip_subscriptions")
    player = relationship("Player", backref="vip_subscriptions")
    order = relationship("Order", backref="vip_subscription")


class RechargeProduct(Base):
    """充值商品配置表"""
    __tablename__ = "recharge_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(64), unique=True, nullable=False)

    # 商品信息
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    product_type = Column(SQLEnum(ProductType), nullable=False)

    # 价格
    price = Column(Float, nullable=False)  # 人民币价格
    original_price = Column(Float, nullable=True)  # 原价(用于显示折扣)

    # 赠送内容
    diamonds = Column(Integer, default=0)  # 钻石数量
    bonus_diamonds = Column(Integer, default=0)  # 额外赠送钻石
    vip_days = Column(Integer, default=0)  # VIP天数
    items = Column(Text, nullable=True)  # JSON格式的物品列表

    # 限制
    daily_limit = Column(Integer, default=-1)  # 每日限购 -1无限
    total_limit = Column(Integer, default=-1)  # 总限购 -1无限
    first_purchase_bonus = Column(Integer, default=0)  # 首充额外赠送

    # 状态
    is_active = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)

    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
