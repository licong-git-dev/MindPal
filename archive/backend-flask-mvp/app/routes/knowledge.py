"""
知识库API路由
"""

from flask import Blueprint, request, jsonify
from app.models import db, DigitalHuman, KnowledgeDoc, User
from app.routes.auth import verify_token
from app.services.rag_service import get_rag_service
from app.services.file_parser import FileParser
from app.utils.quota_checker import check_kb_size_limit
from werkzeug.utils import secure_filename
import os
from datetime import datetime

kb_bp = Blueprint('knowledge', __name__)

# 上传配置
UPLOAD_FOLDER = os.path.join('backend', 'uploads')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'md'}

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
    上传文档并处理RAG向量化

    Form data:
        - dhId: 数字人ID
        - file: 文件
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': '未授权'}), 401

        # 获取参数
        dh_id = request.form.get('dhId')
        if not dh_id:
            return jsonify({'success': False, 'error': '缺少数字人ID'}), 400

        dh_id = int(dh_id)

        # 验证数字人所有权
        dh = DigitalHuman.query.filter_by(id=dh_id, user_id=user.id).first()
        if not dh:
            return jsonify({'success': False, 'error': '数字人不存在或无权限'}), 403

        # 检查文件
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        # 验证文件类型
        if not FileParser.is_supported(file.filename):
            return jsonify({
                'success': False,
                'error': f'不支持的文件格式,仅支持: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # 检查文件大小(先不保存,获取大小)
        file.seek(0, os.SEEK_END)  # 移到文件末尾
        file_size = file.tell()  # 获取文件大小
        file.seek(0)  # 重置指针到开头

        # 检查知识库容量限制
        can_upload, error_info = check_kb_size_limit(user.id, file_size)
        if not can_upload:
            return jsonify({'success': False, **error_info}), 403

        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        file.save(file_path)

        # 获取文件信息
        file_type = FileParser.get_file_type(filename)

        # 创建数据库记录
        doc = KnowledgeDoc(
            dh_id=dh_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_url=file_path,
            status='processing'
        )
        db.session.add(doc)
        db.session.commit()

        # 异步处理RAG
        rag_service = get_rag_service(dh_id)
        result = rag_service.process_document(doc.id, file_path, filename)

        if result['success']:
            # 更新状态
            doc.status = 'completed'
            db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'doc': doc.to_dict(),
                    'chunks_count': result.get('chunks_count', 0),
                    'words': result.get('words', 0)
                },
                'message': '文档上传并处理成功'
            }), 201
        else:
            # 处理失败
            doc.status = 'failed'
            db.session.commit()

            return jsonify({
                'success': False,
                'error': result.get('error', '文档处理失败')
            }), 500

    except Exception as e:
        db.session.rollback()
        print(f"[Knowledge] 上传文档失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@kb_bp.route('/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """删除文档及其向量数据"""
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

        # 删除向量数据
        rag_service = get_rag_service(doc.dh_id)
        rag_service.delete_document(doc_id)

        # 删除文件
        if doc.file_url and os.path.exists(doc.file_url):
            try:
                os.remove(doc.file_url)
            except Exception as e:
                print(f"[Knowledge] 删除文件失败: {e}")

        # 删除数据库记录
        db.session.delete(doc)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '删除成功'
        })

    except Exception as e:
        db.session.rollback()
        print(f"[Knowledge] 删除文档失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
