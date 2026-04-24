"""
MindPal Backend V2 - Payment API
支付系统API端点
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import get_current_user_id
from app.models import User, Player
from app.models.payment import Order, OrderStatus, PaymentMethod, ProductType, RechargeProduct
from app.services.payment import (
    OrderService, get_order_service,
    WechatPayService, get_wechat_pay_service,
    AlipayService, get_alipay_service,
)
from app.schemas import APIResponse


router = APIRouter()


# ==================== Schemas ====================

class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    product_id: str = Field(..., description="商品ID")
    quantity: int = Field(1, ge=1, le=99, description="数量")
    payment_method: str = Field(..., description="支付方式: wechat, alipay")


class OrderResponse(BaseModel):
    """订单响应"""
    order_no: str
    product_name: str
    amount: float
    status: str
    created_at: str
    expired_at: Optional[str] = None
    paid_at: Optional[str] = None


class PaymentResponse(BaseModel):
    """支付响应"""
    order_no: str
    payment_method: str
    pay_url: Optional[str] = None
    pay_params: Optional[dict] = None
    code_url: Optional[str] = None  # 微信二维码


class ProductResponse(BaseModel):
    """商品响应"""
    product_id: str
    name: str
    description: Optional[str]
    product_type: str
    price: float
    original_price: Optional[float]
    diamonds: int
    bonus_diamonds: int
    vip_days: int


# ==================== 充值商品 ====================

@router.get("/products", response_model=APIResponse)
async def get_recharge_products(
    product_type: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取充值商品列表
    """
    order_service = get_order_service(db)

    type_filter = None
    if product_type:
        try:
            type_filter = ProductType(product_type)
        except ValueError:
            pass

    products = await order_service.get_recharge_products(type_filter)

    return APIResponse(
        code=0,
        message="success",
        data=[
            ProductResponse(
                product_id=p.product_id,
                name=p.name,
                description=p.description,
                product_type=p.product_type.value,
                price=p.price,
                original_price=p.original_price,
                diamonds=p.diamonds,
                bonus_diamonds=p.bonus_diamonds,
                vip_days=p.vip_days,
            ).model_dump()
            for p in products
        ]
    )


# ==================== 订单管理 ====================

@router.post("/orders", response_model=APIResponse)
async def create_order(
    request: CreateOrderRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    创建充值订单

    注：Player 是游戏化模块的实体，但订阅购买不依赖游戏角色。
    如当前用户没有 Player 记录（例如纯 AI 陪伴用户），自动创建占位记录
    以满足外键约束。游戏化代码清理后（P2-1）此 fallback 可一起删除。
    """
    # 获取或创建 Player（占位以满足 order.player_id 外键）
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        # 读 User 获取 username 作为 nickname 默认值
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user_obj = user_result.scalar_one_or_none()
        nickname = (user_obj.username if user_obj else None) or f"user_{user_id}"

        player = Player(user_id=user_id, nickname=nickname)
        db.add(player)
        await db.flush()  # 取回 id 而不 commit（和下面创建 order 一起 commit）

    # 获取商品
    stmt = select(RechargeProduct).where(
        RechargeProduct.product_id == request.product_id,
        RechargeProduct.is_active == 1
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 计算金额
    amount = product.price * request.quantity

    # 创建订单
    order_service = get_order_service(db)
    order = await order_service.create_order(
        user_id=user_id,
        player_id=player.id,
        product_type=product.product_type,
        product_id=product.product_id,
        product_name=product.name,
        amount=amount,
        quantity=request.quantity,
    )

    await db.commit()

    # 创建支付
    payment_data = None
    payment_method = PaymentMethod(request.payment_method) if request.payment_method in ['wechat', 'alipay'] else None

    if payment_method == PaymentMethod.WECHAT:
        wechat_pay = get_wechat_pay_service()
        payment_data = await wechat_pay.create_unified_order(
            order_no=order.order_no,
            amount=amount,
            description=product.name,
            trade_type="NATIVE",
        )
    elif payment_method == PaymentMethod.ALIPAY:
        alipay = get_alipay_service()
        pay_url = await alipay.create_trade(
            order_no=order.order_no,
            amount=amount,
            subject=product.name,
        )
        if pay_url:
            payment_data = {"pay_url": pay_url}

    return APIResponse(
        code=0,
        message="success",
        data=PaymentResponse(
            order_no=order.order_no,
            payment_method=request.payment_method,
            pay_url=payment_data.get("pay_url") if payment_data else None,
            pay_params=payment_data if payment_data and "pay_url" not in payment_data else None,
            code_url=payment_data.get("code_url") if payment_data else None,
        ).model_dump()
    )


@router.get("/orders", response_model=APIResponse)
async def get_orders(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取订单列表
    """
    order_service = get_order_service(db)

    status_filter = None
    if status:
        try:
            status_filter = OrderStatus(status)
        except ValueError:
            pass

    orders = await order_service.get_user_orders(
        user_id=user_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return APIResponse(
        code=0,
        message="success",
        data=[
            OrderResponse(
                order_no=o.order_no,
                product_name=o.product_name,
                amount=o.amount,
                status=o.status.value,
                created_at=o.created_at.isoformat() if o.created_at else "",
                expired_at=o.expired_at.isoformat() if o.expired_at else None,
                paid_at=o.paid_at.isoformat() if o.paid_at else None,
            ).model_dump()
            for o in orders
        ]
    )


@router.get("/orders/{order_no}", response_model=APIResponse)
async def get_order(
    order_no: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取订单详情
    """
    order_service = get_order_service(db)
    order = await order_service.get_order_by_no(order_no)

    if not order or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    return APIResponse(
        code=0,
        message="success",
        data=OrderResponse(
            order_no=order.order_no,
            product_name=order.product_name,
            amount=order.amount,
            status=order.status.value,
            created_at=order.created_at.isoformat() if order.created_at else "",
            expired_at=order.expired_at.isoformat() if order.expired_at else None,
            paid_at=order.paid_at.isoformat() if order.paid_at else None,
        ).model_dump()
    )


@router.post("/orders/{order_no}/cancel", response_model=APIResponse)
async def cancel_order(
    order_no: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    取消订单
    """
    order_service = get_order_service(db)
    order = await order_service.get_order_by_no(order_no)

    if not order or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    success = await order_service.cancel_order(order)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel this order")

    await db.commit()

    return APIResponse(
        code=0,
        message="Order cancelled"
    )


# ==================== 支付回调 ====================

@router.post("/notify/wechat", response_class=PlainTextResponse)
async def wechat_pay_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    微信支付回调
    """
    body = await request.body()
    xml_data = body.decode('utf-8')

    wechat_pay = get_wechat_pay_service()
    notify_data = wechat_pay.verify_notify(xml_data)

    if not notify_data:
        return wechat_pay.generate_notify_response(False)

    order_no = notify_data.get("out_trade_no")
    transaction_id = notify_data.get("transaction_id")
    result_code = notify_data.get("result_code")

    if result_code != "SUCCESS":
        return wechat_pay.generate_notify_response(True)

    # 处理订单
    order_service = get_order_service(db)
    order = await order_service.get_order_by_no(order_no)

    if not order:
        return wechat_pay.generate_notify_response(True)

    if order.status == OrderStatus.PENDING:
        # 标记已支付
        await order_service.mark_paid(order, PaymentMethod.WECHAT, transaction_id)
        # 发货
        await order_service.deliver_order(order)
        await db.commit()

    return wechat_pay.generate_notify_response(True)


@router.post("/notify/alipay", response_class=PlainTextResponse)
async def alipay_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    支付宝支付回调
    """
    form = await request.form()
    params = dict(form)

    alipay = get_alipay_service()

    if not alipay.verify_notify(params):
        return alipay.get_notify_response(False)

    order_no = params.get("out_trade_no")
    trade_no = params.get("trade_no")
    trade_status = params.get("trade_status")

    if trade_status not in ["TRADE_SUCCESS", "TRADE_FINISHED"]:
        return alipay.get_notify_response(True)

    # 处理订单
    order_service = get_order_service(db)
    order = await order_service.get_order_by_no(order_no)

    if not order:
        return alipay.get_notify_response(True)

    if order.status == OrderStatus.PENDING:
        # 标记已支付
        await order_service.mark_paid(order, PaymentMethod.ALIPAY, trade_no)
        # 发货
        await order_service.deliver_order(order)
        await db.commit()

    return alipay.get_notify_response(True)


# ==================== VIP信息 ====================

@router.get("/vip/status", response_model=APIResponse)
async def get_vip_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取VIP状态
    """
    from app.models.payment import VIPSubscription
    from datetime import datetime

    # 获取角色
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 获取VIP订阅
    stmt = select(VIPSubscription).where(
        VIPSubscription.player_id == player.id,
        VIPSubscription.is_active == 1,
        VIPSubscription.expired_at > datetime.utcnow()
    ).order_by(VIPSubscription.expired_at.desc())

    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()

    if subscription:
        return APIResponse(
            code=0,
            message="success",
            data={
                "is_vip": True,
                "vip_level": subscription.vip_level,
                "started_at": subscription.started_at.isoformat(),
                "expired_at": subscription.expired_at.isoformat(),
                "auto_renew": subscription.auto_renew == 1,
            }
        )
    else:
        return APIResponse(
            code=0,
            message="success",
            data={
                "is_vip": False,
                "vip_level": 0,
            }
        )


# ==================== 模拟支付 (开发测试) ====================

from app.services.payment.mock_payment import get_mock_payment_service


@router.post("/mock/create", response_model=APIResponse)
async def create_mock_payment(
    request: CreateOrderRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    创建模拟支付订单 (开发测试用)

    流程：创建订单 -> 返回模拟支付链接 -> 访问链接完成支付
    """
    # 获取角色
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 获取商品
    stmt = select(RechargeProduct).where(
        RechargeProduct.product_id == request.product_id,
        RechargeProduct.is_active == 1
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 计算金额
    amount = product.price * request.quantity

    # 创建订单
    order_service = get_order_service(db)
    order = await order_service.create_order(
        user_id=user_id,
        player_id=player.id,
        product_type=product.product_type,
        product_id=product.product_id,
        product_name=product.name,
        amount=amount,
        quantity=request.quantity,
    )

    await db.commit()

    # 创建模拟支付
    mock_pay = get_mock_payment_service()
    payment_info = await mock_pay.create_payment(
        order_no=order.order_no,
        amount=amount,
        description=product.name,
        payment_method="mock",
    )

    return APIResponse(
        code=0,
        message="success",
        data={
            "order_no": order.order_no,
            "amount": amount,
            "product_name": product.name,
            **payment_info,
        }
    )


@router.get("/mock/pay/{order_no}", response_model=APIResponse)
async def mock_pay_order(
    order_no: str,
    db: AsyncSession = Depends(get_db),
):
    """
    模拟支付确认页面 (开发测试用)

    访问此端点即完成支付
    """
    # 获取订单
    order_service = get_order_service(db)
    order = await order_service.get_order_by_no(order_no)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        return APIResponse(
            code=0,
            message="订单已处理",
            data={"order_no": order_no, "status": order.status.value}
        )

    # 确认模拟支付
    mock_pay = get_mock_payment_service()
    result = await mock_pay.confirm_payment(order_no)

    if result["success"]:
        # 标记订单已支付
        await order_service.mark_paid(order, PaymentMethod.WECHAT, result["trade_no"])
        # 发货
        await order_service.deliver_order(order)
        await db.commit()

        return APIResponse(
            code=0,
            message="模拟支付成功！商品已发放",
            data={
                "order_no": order_no,
                "trade_no": result["trade_no"],
                "amount": result["amount"],
                "status": "paid",
                "delivered": True,
            }
        )
    else:
        raise HTTPException(status_code=400, detail=result["message"])


@router.get("/mock/status/{order_no}", response_model=APIResponse)
async def get_mock_payment_status(
    order_no: str,
    user_id: int = Depends(get_current_user_id),
):
    """
    查询模拟支付状态
    """
    mock_pay = get_mock_payment_service()
    result = await mock_pay.query_payment(order_no)

    return APIResponse(
        code=0,
        message="success",
        data=result
    )


@router.post("/test/add-diamonds", response_model=APIResponse)
async def test_add_diamonds(
    amount: int = 100,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    测试接口：直接添加钻石 (开发测试用)
    """
    # 获取角色
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 添加钻石
    player.diamonds = (player.diamonds or 0) + amount
    await db.commit()

    return APIResponse(
        code=0,
        message=f"成功添加 {amount} 钻石",
        data={
            "added": amount,
            "total_diamonds": player.diamonds,
        }
    )


@router.post("/test/add-gold", response_model=APIResponse)
async def test_add_gold(
    amount: int = 1000,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    测试接口：直接添加金币 (开发测试用)
    """
    # 获取角色
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 添加金币
    player.gold = (player.gold or 0) + amount
    await db.commit()

    return APIResponse(
        code=0,
        message=f"成功添加 {amount} 金币",
        data={
            "added": amount,
            "total_gold": player.gold,
        }
    )
