"""
MindPal Backend Server
基于Flask + 阿里云通义千问的数字人对话平台后端
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 初始化Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data/mindpal.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))  # 10MB
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

# CORS配置
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": allowed_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 初始化数据库
from app.models import db
db.init_app(app)

# 创建数据库表
with app.app_context():
    db.create_all()

# 注册路由蓝图
from app.routes.auth import auth_bp
from app.routes.digital_humans import dh_bp
from app.routes.chat import chat_bp
from app.routes.knowledge import kb_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(dh_bp, url_prefix='/api/digital-humans')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(kb_bp, url_prefix='/api/knowledge')

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'MindPal Backend',
        'version': '1.0.0'
    })

# 根路径
@app.route('/', methods=['GET'])
def index():
    """API根路径"""
    return jsonify({
        'message': 'Welcome to MindPal API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth',
            'digital_humans': '/api/digital-humans',
            'chat': '/api/chat',
            'knowledge': '/api/knowledge'
        }
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
