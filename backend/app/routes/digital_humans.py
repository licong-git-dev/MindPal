"""
数字人管理API路由
"""

from flask import Blueprint, request, jsonify
from app.models import db, DigitalHuman, User
from app.routes.auth import verify_token
from datetime import datetime

dh_bp = Blueprint('digital_humans', __name__)


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


@dh_bp.route('', methods=['GET'])
def list_digital_humans():
    """获取当前用户的所有数字人"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        dhs = DigitalHuman.query.filter_by(user_id=user.id).order_by(DigitalHuman.created_at.desc()).all()

        return jsonify({
            'success': True,
            'data': [dh.to_dict() for dh in dhs]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dh_bp.route('/<int:dh_id>', methods=['GET'])
def get_digital_human(dh_id):
    """获取单个数字人详情"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        dh = DigitalHuman.query.filter_by(id=dh_id, user_id=user.id).first()
        if not dh:
            return jsonify({'success': False, 'error': '数字人不存在'}), 404

        return jsonify({
            'success': True,
            'data': dh.to_dict()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dh_bp.route('', methods=['POST'])
def create_digital_human():
    """创建新数字人"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        data = request.get_json()

        # 创建数字人
        dh = DigitalHuman(
            user_id=user.id,
            name=data.get('name'),
            avatar_type=data.get('avatar'),
            avatar_emoji=data.get('avatarEmoji'),
            avatar_custom_url=data.get('avatarCustom'),
            personality=data.get('personality'),
            custom_personality=data.get('customPersonality'),
            voice=data.get('voice')
        )

        # 设置特质
        if data.get('traits'):
            dh.set_traits(data['traits'])

        # 设置声音参数
        if data.get('voiceParams'):
            dh.set_voice_params(data['voiceParams'])

        db.session.add(dh)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': dh.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@dh_bp.route('/<int:dh_id>', methods=['DELETE'])
def delete_digital_human(dh_id):
    """删除数字人"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        dh = DigitalHuman.query.filter_by(id=dh_id, user_id=user.id).first()
        if not dh:
            return jsonify({'success': False, 'error': '数字人不存在'}), 404

        db.session.delete(dh)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '删除成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
