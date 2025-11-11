"""
数据库模型
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(11), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # 关系
    digital_humans = db.relationship('DigitalHuman', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码（加密）"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DigitalHuman(db.Model):
    """数字人表"""
    __tablename__ = 'digital_humans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    avatar_type = db.Column(db.String(50))
    avatar_emoji = db.Column(db.Text)
    avatar_custom_url = db.Column(db.Text)
    personality = db.Column(db.String(50))
    traits = db.Column(db.Text)  # JSON string
    custom_personality = db.Column(db.Text)
    voice = db.Column(db.String(50))
    voice_params = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_chat_at = db.Column(db.DateTime)
    message_count = db.Column(db.Integer, default=0)

    # 关系
    messages = db.relationship('Message', backref='digital_human', lazy=True, cascade='all, delete-orphan')
    knowledge_docs = db.relationship('KnowledgeDoc', backref='digital_human', lazy=True, cascade='all, delete-orphan')

    def get_traits(self):
        """获取性格特质（字典）"""
        return json.loads(self.traits) if self.traits else {}

    def set_traits(self, traits_dict):
        """设置性格特质"""
        self.traits = json.dumps(traits_dict, ensure_ascii=False)

    def get_voice_params(self):
        """获取声音参数（字典）"""
        return json.loads(self.voice_params) if self.voice_params else {}

    def set_voice_params(self, params_dict):
        """设置声音参数"""
        self.voice_params = json.dumps(params_dict, ensure_ascii=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'avatarEmoji': self.avatar_emoji,
            'avatarType': self.avatar_type,
            'personality': self.personality,
            'traits': self.get_traits(),
            'customPersonality': self.custom_personality,
            'voice': self.voice,
            'voiceParams': self.get_voice_params(),
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastChatAt': self.last_chat_at.isoformat() if self.last_chat_at else None,
            'messageCount': self.message_count
        }


class Message(db.Model):
    """对话消息表"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    dh_id = db.Column(db.Integer, db.ForeignKey('digital_humans.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    emotion = db.Column(db.String(20))  # 'happy', 'sad', 'calm', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'emotion': self.emotion,
            'timestamp': self.created_at.isoformat() if self.created_at else None
        }


class KnowledgeDoc(db.Model):
    """知识库文档表"""
    __tablename__ = 'knowledge_docs'

    id = db.Column(db.Integer, primary_key=True)
    dh_id = db.Column(db.Integer, db.ForeignKey('digital_humans.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20))
    file_size = db.Column(db.Integer)
    file_url = db.Column(db.Text)
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'fileType': self.file_type,
            'fileSize': self.file_size,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
