"""
订阅系统API路由
"""

from flask import Blueprint, request, jsonify
from app.models import db, User, Subscription, UserQuota
from app.routes.auth import token_required
from datetime import datetime, timedelta

subscription_bp = Blueprint('subscription', __name__)


@subscription_bp.route('/create', methods=['POST'])
@token_required
def create_subscription(current_user):
    """
    创建订阅
    POST /api/subscription/create
    {
        "planType": "monthly" | "yearly",
        "paymentId": "支付订单ID"
    }
    """
    try:
        data = request.get_json()
        plan_type = data.get('planType')
        payment_id = data.get('paymentId')

        if not plan_type or plan_type not in ['monthly', 'yearly']:
            return jsonify({'error': '无效的套餐类型'}), 400

        # 检查是否已有活跃订阅
        existing_sub = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()

        if existing_sub and existing_sub.is_active():
            return jsonify({'error': '您已有活跃的订阅'}), 400

        # 计算订阅结束时间
        start_date = datetime.utcnow()
        if plan_type == 'monthly':
            end_date = start_date + timedelta(days=30)
        else:  # yearly
            end_date = start_date + timedelta(days=365)

        # 创建订阅记录
        subscription = Subscription(
            user_id=current_user.id,
            plan_type=plan_type,
            start_date=start_date,
            end_date=end_date,
            status='active',
            payment_id=payment_id,
            auto_renew=True
        )

        db.session.add(subscription)

        # 更新用户配额
        quota = UserQuota.query.filter_by(user_id=current_user.id).first()
        if not quota:
            quota = UserQuota(user_id=current_user.id)
            db.session.add(quota)

        # 会员版配额
        quota.dh_limit = 10
        quota.kb_size_limit = 500
        quota.daily_chat_limit = -1  # 无限
        quota.daily_voice_limit = -1  # 无限

        db.session.commit()

        return jsonify({
            'message': '订阅成功',
            'subscription': subscription.to_dict(),
            'quota': quota.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[Subscription] 创建订阅失败: {e}")
        return jsonify({'error': '创建订阅失败'}), 500


@subscription_bp.route('/status', methods=['GET'])
@token_required
def get_subscription_status(current_user):
    """
    查询订阅状态
    GET /api/subscription/status
    """
    try:
        # 查询当前活跃订阅
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).order_by(Subscription.created_at.desc()).first()

        # 查询配额
        quota = UserQuota.query.filter_by(user_id=current_user.id).first()
        if not quota:
            # 创建默认免费版配额
            quota = UserQuota(user_id=current_user.id)
            db.session.add(quota)
            db.session.commit()

        # 检查订阅是否过期
        if subscription and not subscription.is_active():
            subscription.status = 'expired'
            # 降级为免费版配额
            quota.dh_limit = 5
            quota.kb_size_limit = 50
            quota.daily_chat_limit = 100
            quota.daily_voice_limit = 10
            db.session.commit()

        # 重置每日配额（如果需要）
        quota.reset_daily_quota()
        db.session.commit()

        # 统计当前使用情况
        from app.models import DigitalHuman, KnowledgeDoc
        dh_count = DigitalHuman.query.filter_by(user_id=current_user.id).count()

        # 计算知识库总大小
        kb_total_size = 0
        docs = db.session.query(KnowledgeDoc).join(
            DigitalHuman, KnowledgeDoc.dh_id == DigitalHuman.id
        ).filter(DigitalHuman.user_id == current_user.id).all()
        for doc in docs:
            if doc.file_size:
                kb_total_size += doc.file_size

        kb_total_size_mb = round(kb_total_size / (1024 * 1024), 2)

        return jsonify({
            'subscription': subscription.to_dict() if subscription else None,
            'quota': quota.to_dict(),
            'usage': {
                'dhCount': dh_count,
                'dhLimit': quota.dh_limit,
                'kbSizeMB': kb_total_size_mb,
                'kbSizeLimit': quota.kb_size_limit,
                'dailyChatUsed': quota.daily_chat_used,
                'dailyChatLimit': quota.daily_chat_limit,
                'dailyVoiceUsed': quota.daily_voice_used,
                'dailyVoiceLimit': quota.daily_voice_limit
            }
        }), 200

    except Exception as e:
        print(f"[Subscription] 查询订阅状态失败: {e}")
        return jsonify({'error': '查询订阅状态失败'}), 500


@subscription_bp.route('/cancel', methods=['POST'])
@token_required
def cancel_subscription(current_user):
    """
    取消订阅
    POST /api/subscription/cancel
    """
    try:
        # 查询当前活跃订阅
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).order_by(Subscription.created_at.desc()).first()

        if not subscription:
            return jsonify({'error': '没有活跃的订阅'}), 404

        # 设置为不自动续费（保留到当前周期结束）
        subscription.auto_renew = False
        subscription.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': '订阅已取消，将在当前订阅周期结束后停止',
            'subscription': subscription.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[Subscription] 取消订阅失败: {e}")
        return jsonify({'error': '取消订阅失败'}), 500


@subscription_bp.route('/quota', methods=['GET'])
@token_required
def get_quota(current_user):
    """
    获取配额信息
    GET /api/subscription/quota
    """
    try:
        quota = UserQuota.query.filter_by(user_id=current_user.id).first()
        if not quota:
            # 创建默认免费版配额
            quota = UserQuota(user_id=current_user.id)
            db.session.add(quota)
            db.session.commit()

        # 重置每日配额（如果需要）
        quota.reset_daily_quota()
        db.session.commit()

        return jsonify(quota.to_dict()), 200

    except Exception as e:
        print(f"[Subscription] 获取配额失败: {e}")
        return jsonify({'error': '获取配额失败'}), 500


@subscription_bp.route('/history', methods=['GET'])
@token_required
def get_subscription_history(current_user):
    """
    获取订阅历史
    GET /api/subscription/history
    """
    try:
        subscriptions = Subscription.query.filter_by(
            user_id=current_user.id
        ).order_by(Subscription.created_at.desc()).all()

        return jsonify({
            'subscriptions': [sub.to_dict() for sub in subscriptions]
        }), 200

    except Exception as e:
        print(f"[Subscription] 获取订阅历史失败: {e}")
        return jsonify({'error': '获取订阅历史失败'}), 500


@subscription_bp.route('/upgrade-preview', methods=['POST'])
@token_required
def upgrade_preview(current_user):
    """
    预览升级后的配额
    POST /api/subscription/upgrade-preview
    {
        "planType": "monthly" | "yearly"
    }
    """
    try:
        data = request.get_json()
        plan_type = data.get('planType')

        if not plan_type or plan_type not in ['monthly', 'yearly']:
            return jsonify({'error': '无效的套餐类型'}), 400

        # 会员版配额预览
        preview_quota = {
            'dhLimit': 10,
            'kbSizeLimit': 500,
            'dailyChatLimit': -1,  # 无限
            'dailyVoiceLimit': -1,  # 无限
            'features': [
                '10个数字人',
                '知识库500MB',
                '无限对话',
                '无限语音',
                '3D写实形象',
                '202种方言支持',
                '深度情绪分析',
                '优先体验新功能'
            ]
        }

        price = 19.9 if plan_type == 'monthly' else 199
        duration = '30天' if plan_type == 'monthly' else '365天'

        return jsonify({
            'planType': plan_type,
            'price': price,
            'duration': duration,
            'quota': preview_quota
        }), 200

    except Exception as e:
        print(f"[Subscription] 升级预览失败: {e}")
        return jsonify({'error': '升级预览失败'}), 500
