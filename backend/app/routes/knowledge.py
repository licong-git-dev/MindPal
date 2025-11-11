"""
知识库API路由
"""

from flask import Blueprint, request, jsonify
from app.models import db, DigitalHuman, KnowledgeDoc, User
from app.routes.auth import verify_token
import os

kb_bp = Blueprint('knowledge', __name__)


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


@kb_bp.route('/<int:dh_id>', methods=['GET'])
def list_documents(dh_id):
    """获取知识库文档列表"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        # 验证数字人
        dh = DigitalHuman.query.filter_by(id=dh_id, user_id=user.id).first()
        if not dh:
            return jsonify({'success': False, 'error': '数字人不存在'}), 404

        docs = KnowledgeDoc.query.filter_by(dh_id=dh_id).order_by(KnowledgeDoc.created_at.desc()).all()

        return jsonify({
            'success': True,
            'data': {
                'docs': [doc.to_dict() for doc in docs]
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@kb_bp.route('/upload', methods=['POST'])
def upload_document():
    """
    上传文档（P1阶段实现）

    当前返回模拟数据
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        # TODO: 实现文件上传、解析、向量化
        # 当前返回成功响应
        return jsonify({
            'success': True,
            'message': '文档上传功能将在P1阶段实现'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@kb_bp.route('/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """删除文档"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        # 查找文档
        doc = KnowledgeDoc.query.get(doc_id)
        if not doc:
            return jsonify({'success': False, 'error': '文档不存在'}), 404

        # 验证权限
        dh = DigitalHuman.query.filter_by(id=doc.dh_id, user_id=user.id).first()
        if not dh:
            return jsonify({'success': False, 'error': '无权限'}), 403

        db.session.delete(doc)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '删除成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
