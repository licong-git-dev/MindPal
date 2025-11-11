"""
用户认证API路由
"""

from flask import Blueprint, request, jsonify
from app.models import db, User
from datetime import datetime, timedelta
import jwt
import os

auth_bp = Blueprint('auth', __name__)


def generate_token(user_id):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)  # 7天过期
    }
    token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm='HS256')
    return token


def verify_token(token):
    """验证JWT token"""
    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册

    请求body:
    {
        "phone": "13800138000",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()

        phone = data.get('phone')
        password = data.get('password')

        # 验证输入
        if not phone or not password:
            return jsonify({
                'success': False,
                'error': '手机号和密码不能为空'
            }), 400

        # 验证手机号格式
        if len(phone) != 11 or not phone.isdigit():
            return jsonify({
                'success': False,
                'error': '手机号格式不正确'
            }), 400

        # 检查手机号是否已存在
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': '该手机号已注册'
            }), 400

        # 创建新用户
        user = User(phone=phone)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录

    请求body:
    {
        "phone": "13800138000",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()

        phone = data.get('phone')
        password = data.get('password')

        # 验证输入
        if not phone or not password:
            return jsonify({
                'success': False,
                'error': '手机号和密码不能为空'
            }), 400

        # 查找用户
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({
                'success': False,
                'error': '用户不存在'
            }), 404

        # 验证密码
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'error': '密码错误'
            }), 401

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()

        # 生成token
        token = generate_token(user.id)

        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/verify', methods=['GET'])
def verify():
    """验证token是否有效"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'success': False,
                'error': '缺少Authorization header'
            }), 401

        token = auth_header.replace('Bearer ', '')
        user_id = verify_token(token)

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Token无效或已过期'
            }), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': '用户不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
