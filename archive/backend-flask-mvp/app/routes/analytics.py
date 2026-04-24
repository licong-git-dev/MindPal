"""
数据埋点API路由
"""

from flask import Blueprint, request, jsonify
from app.models import db, Analytics, User, Message
from app.routes.auth import token_required
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import uuid

analytics_bp = Blueprint('analytics', __name__)


def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr


@analytics_bp.route('/track', methods=['POST'])
def track_event():
    """
    记录埋点事件
    POST /api/analytics/track
    {
        "eventName": "page_view",
        "userId": 1,  // 可选
        "sessionId": "uuid",
        "metadata": {
            "page": "dh-list",
            "duration": 1500
        }
    }
    """
    try:
        data = request.get_json()
        event_name = data.get('eventName')

        if not event_name:
            return jsonify({'error': '缺少事件名称'}), 400

        # 创建埋点记录
        event = Analytics(
            event_name=event_name,
            user_id=data.get('userId'),
            session_id=data.get('sessionId') or str(uuid.uuid4()),
            user_agent=request.headers.get('User-Agent', ''),
            ip_address=get_client_ip(),
            referrer=request.headers.get('Referer', '')
        )

        # 设置元数据
        if data.get('metadata'):
            event.set_metadata(data['metadata'])

        db.session.add(event)
        db.session.commit()

        return jsonify({
            'success': True,
            'eventId': event.id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[Analytics] 记录埋点失败: {e}")
        return jsonify({'error': '记录埋点失败'}), 500


@analytics_bp.route('/batch', methods=['POST'])
def track_batch():
    """
    批量记录埋点事件
    POST /api/analytics/batch
    {
        "events": [
            {"eventName": "page_view", "metadata": {...}},
            {"eventName": "button_click", "metadata": {...}}
        ]
    }
    """
    try:
        data = request.get_json()
        events_data = data.get('events', [])

        if not events_data:
            return jsonify({'error': '缺少事件数据'}), 400

        events = []
        session_id = str(uuid.uuid4())

        for event_data in events_data:
            event = Analytics(
                event_name=event_data.get('eventName'),
                user_id=event_data.get('userId'),
                session_id=event_data.get('sessionId') or session_id,
                user_agent=request.headers.get('User-Agent', ''),
                ip_address=get_client_ip(),
                referrer=request.headers.get('Referer', '')
            )

            if event_data.get('metadata'):
                event.set_metadata(event_data['metadata'])

            events.append(event)

        db.session.add_all(events)
        db.session.commit()

        return jsonify({
            'success': True,
            'count': len(events)
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[Analytics] 批量记录埋点失败: {e}")
        return jsonify({'error': '批量记录埋点失败'}), 500


@analytics_bp.route('/dashboard', methods=['GET'])
@token_required
def get_dashboard(current_user):
    """
    获取数据分析面板
    GET /api/analytics/dashboard?range=7
    """
    try:
        # 仅管理员可访问（简化版：允许所有登录用户查看自己的数据）
        days = int(request.args.get('range', 7))
        start_date = datetime.utcnow() - timedelta(days=days)

        # 总用户数
        total_users = User.query.count()

        # 新增用户数（最近N天）
        new_users = User.query.filter(User.created_at >= start_date).count()

        # DAU (今日活跃用户数)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        dau = db.session.query(func.count(func.distinct(Analytics.user_id))).filter(
            Analytics.created_at >= today_start,
            Analytics.user_id.isnot(None)
        ).scalar() or 0

        # 总对话次数
        total_messages = Message.query.count()

        # 今日对话次数
        today_messages = Message.query.filter(Message.created_at >= today_start).count()

        # 最近N天的每日统计
        daily_stats = []
        for i in range(days):
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            # 当日活跃用户数
            daily_users = db.session.query(func.count(func.distinct(Analytics.user_id))).filter(
                and_(
                    Analytics.created_at >= day_start,
                    Analytics.created_at < day_end,
                    Analytics.user_id.isnot(None)
                )
            ).scalar() or 0

            # 当日新增用户
            daily_new_users = User.query.filter(
                and_(
                    User.created_at >= day_start,
                    User.created_at < day_end
                )
            ).count()

            # 当日对话次数
            daily_chats = Message.query.filter(
                and_(
                    Message.created_at >= day_start,
                    Message.created_at < day_end
                )
            ).count()

            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'activeUsers': daily_users,
                'newUsers': daily_new_users,
                'chats': daily_chats
            })

        # 事件统计（最近N天）
        event_counts = db.session.query(
            Analytics.event_name,
            func.count(Analytics.id).label('count')
        ).filter(
            Analytics.created_at >= start_date
        ).group_by(Analytics.event_name).all()

        event_stats = {event: count for event, count in event_counts}

        # WACU (Weekly Active Conversation Users) - 本周至少5次对话的用户数
        week_start = datetime.utcnow() - timedelta(days=7)
        wacu_users = db.session.query(
            Message.dh_id,
            func.count(Message.id).label('msg_count')
        ).filter(
            Message.created_at >= week_start
        ).group_by(Message.dh_id).having(
            func.count(Message.id) >= 5
        ).count()

        return jsonify({
            'summary': {
                'totalUsers': total_users,
                'newUsers': new_users,
                'dau': dau,
                'totalMessages': total_messages,
                'todayMessages': today_messages,
                'wacu': wacu_users
            },
            'dailyStats': list(reversed(daily_stats)),  # 从旧到新
            'eventStats': event_stats
        }), 200

    except Exception as e:
        print(f"[Analytics] 获取面板数据失败: {e}")
        return jsonify({'error': '获取面板数据失败'}), 500


@analytics_bp.route('/events', methods=['GET'])
@token_required
def get_events(current_user):
    """
    获取埋点事件列表
    GET /api/analytics/events?event=page_view&limit=100
    """
    try:
        event_name = request.args.get('event')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        query = Analytics.query

        if event_name:
            query = query.filter_by(event_name=event_name)

        # 只返回当前用户的事件（如果是管理员可以看全部）
        if current_user.id != 1:  # 假设ID=1是管理员
            query = query.filter_by(user_id=current_user.id)

        events = query.order_by(Analytics.created_at.desc()).limit(limit).offset(offset).all()
        total = query.count()

        return jsonify({
            'events': [event.to_dict() for event in events],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        print(f"[Analytics] 获取事件列表失败: {e}")
        return jsonify({'error': '获取事件列表失败'}), 500


@analytics_bp.route('/funnel', methods=['GET'])
@token_required
def get_funnel(current_user):
    """
    获取转化漏斗数据
    GET /api/analytics/funnel?range=30
    """
    try:
        days = int(request.args.get('range', 30))
        start_date = datetime.utcnow() - timedelta(days=days)

        # 访客数（page_view事件的唯一session）
        visitors = db.session.query(func.count(func.distinct(Analytics.session_id))).filter(
            and_(
                Analytics.event_name == 'page_view',
                Analytics.created_at >= start_date
            )
        ).scalar() or 0

        # 注册用户数
        registers = User.query.filter(User.created_at >= start_date).count()

        # 创建数字人的用户数
        creators = db.session.query(func.count(func.distinct(Analytics.user_id))).filter(
            and_(
                Analytics.event_name == 'dh_create',
                Analytics.created_at >= start_date
            )
        ).scalar() or 0

        # 发起对话的用户数
        chatters = db.session.query(func.count(func.distinct(Analytics.user_id))).filter(
            and_(
                Analytics.event_name == 'chat_send',
                Analytics.created_at >= start_date
            )
        ).scalar() or 0

        # 付费用户数
        payers = db.session.query(func.count(func.distinct(Analytics.user_id))).filter(
            and_(
                Analytics.event_name == 'payment_success',
                Analytics.created_at >= start_date
            )
        ).scalar() or 0

        # 计算转化率
        funnel_data = [
            {
                'stage': '访客',
                'count': visitors,
                'rate': 100.0
            },
            {
                'stage': '注册',
                'count': registers,
                'rate': round((registers / visitors * 100), 2) if visitors > 0 else 0
            },
            {
                'stage': '创建数字人',
                'count': creators,
                'rate': round((creators / registers * 100), 2) if registers > 0 else 0
            },
            {
                'stage': '活跃对话',
                'count': chatters,
                'rate': round((chatters / creators * 100), 2) if creators > 0 else 0
            },
            {
                'stage': '付费',
                'count': payers,
                'rate': round((payers / chatters * 100), 2) if chatters > 0 else 0
            }
        ]

        return jsonify({
            'funnel': funnel_data,
            'overallConversion': round((payers / visitors * 100), 2) if visitors > 0 else 0
        }), 200

    except Exception as e:
        print(f"[Analytics] 获取漏斗数据失败: {e}")
        return jsonify({'error': '获取漏斗数据失败'}), 500
