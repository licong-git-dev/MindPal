"""
对话API路由
"""

from flask import Blueprint, request, jsonify, Response, current_app
from app.models import db, DigitalHuman, Message, User
from app.routes.auth import verify_token
from app.services.qianwen_service import chat_with_qianwen, analyze_emotion
from datetime import datetime
import json

chat_bp = Blueprint('chat', __name__)


def get_current_user():
    """获取当前登录用户"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    token = auth_header.replace('Bearer ', '')
    user_id = verify_token(token)
    if not user_id:
        return None

    return User.query.get(user_id)


@chat_bp.route('', methods=['POST'])
def chat():
    """
    发送消息并获取AI回复（流式）

    请求body:
    {
        "dhId": 1,
        "message": "你好"
    }
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        data = request.get_json()
        dh_id = data.get('dhId')
        user_message = data.get('message')

        if not dh_id or not user_message:
            return jsonify({'success': False, 'error': '参数错误'}), 400

        # 获取数字人
        dh = DigitalHuman.query.filter_by(id=dh_id, user_id=user.id).first()
        if not dh:
            return jsonify({'success': False, 'error': '数字人不存在'}), 404

        # 保存用户消息
        user_msg = Message(
            dh_id=dh_id,
            role='user',
            content=user_message
        )
        db.session.add(user_msg)

        # 获取对话历史（最近10轮）
        history_messages = Message.query.filter_by(dh_id=dh_id)\
            .order_by(Message.created_at.desc())\
            .limit(20)\
            .all()
        history_messages.reverse()

        # 构建消息列表
        messages = []
        for msg in history_messages:
            messages.append({
                'role': msg.role,
                'content': msg.content
            })

        # 添加当前消息
        messages.append({
            'role': 'user',
            'content': user_message
        })

        # 获取app实例用于生成器中的数据库操作
        app = current_app._get_current_object()

        # 流式响应
        def generate():
            full_response = ""

            try:
                # 调用通义千问
                for chunk in chat_with_qianwen(messages, dh.to_dict(), stream=True):
                    full_response += chunk
                    # SSE格式
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"

                # 分析情绪
                emotion = analyze_emotion(user_message)

                # 保存AI回复（在应用上下文中）
                with app.app_context():
                    ai_msg = Message(
                        dh_id=dh_id,
                        role='assistant',
                        content=full_response,
                        emotion=emotion
                    )
                    db.session.add(ai_msg)

                    # 更新数字人统计
                    dh_obj = DigitalHuman.query.get(dh_id)
                    if dh_obj:
                        dh_obj.last_chat_at = datetime.utcnow()
                        dh_obj.message_count += 2  # 用户消息 + AI消息

                    db.session.commit()

                # 发送完成信号
                yield f"data: {json.dumps({'done': True, 'emotion': emotion}, ensure_ascii=False)}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/history/<int:dh_id>', methods=['GET'])
def get_history(dh_id):
    """
    获取对话历史

    Query参数:
    - limit: 返回消息数量（默认50）
    - offset: 偏移量（默认0）
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        # 验证数字人
        dh = DigitalHuman.query.filter_by(id=dh_id, user_id=user.id).first()
        if not dh:
            return jsonify({'success': False, 'error': '数字人不存在'}), 404

        # 获取参数
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        # 查询消息
        messages = Message.query.filter_by(dh_id=dh_id)\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

        messages.reverse()  # 按时间正序

        total = Message.query.filter_by(dh_id=dh_id).count()

        return jsonify({
            'success': True,
            'data': {
                'messages': [msg.to_dict() for msg in messages],
                'total': total
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/history/<int:dh_id>', methods=['DELETE'])
def clear_history(dh_id):
    """清除对话历史"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        # 验证数字人
        dh = DigitalHuman.query.filter_by(id=dh_id, user_id=user.id).first()
        if not dh:
            return jsonify({'success': False, 'error': '数字人不存在'}), 404

        # 删除所有消息
        Message.query.filter_by(dh_id=dh_id).delete()

        # 重置统计
        dh.message_count = 0

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '对话历史已清除'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
