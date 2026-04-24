"""
配额检查工具
用于检查用户是否超出配额限制
"""

from flask import jsonify
from app.models import db, UserQuota, DigitalHuman, KnowledgeDoc
from functools import wraps


def quota_check_chat(f):
    """
    对话配额检查装饰器
    检查用户每日对话次数是否达到限制
    """
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        quota = UserQuota.query.filter_by(user_id=current_user.id).first()
        if not quota:
            # 如果没有配额记录,创建默认免费版配额
            quota = UserQuota(user_id=current_user.id)
            db.session.add(quota)
            db.session.commit()

        # 检查是否可以对话
        if not quota.can_chat():
            return jsonify({
                'error': '您今日的对话次数已用完',
                'quota': quota.to_dict(),
                'message': '升级会员可享受无限对话'
            }), 429  # 429 Too Many Requests

        # 增加对话计数
        quota.increment_chat()
        db.session.commit()

        return f(current_user, *args, **kwargs)

    return decorated


def quota_check_voice(f):
    """
    语音配额检查装饰器
    检查用户每日语音次数是否达到限制
    """
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        quota = UserQuota.query.filter_by(user_id=current_user.id).first()
        if not quota:
            quota = UserQuota(user_id=current_user.id)
            db.session.add(quota)
            db.session.commit()

        if not quota.can_voice():
            return jsonify({
                'error': '您今日的语音次数已用完',
                'quota': quota.to_dict(),
                'message': '升级会员可享受无限语音'
            }), 429

        quota.increment_voice()
        db.session.commit()

        return f(current_user, *args, **kwargs)

    return decorated


def check_dh_limit(user_id):
    """
    检查数字人数量是否达到限制
    返回: (是否可以创建, 错误信息)
    """
    quota = UserQuota.query.filter_by(user_id=user_id).first()
    if not quota:
        quota = UserQuota(user_id=user_id)
        db.session.add(quota)
        db.session.commit()

    dh_count = DigitalHuman.query.filter_by(user_id=user_id).count()

    if dh_count >= quota.dh_limit:
        return False, {
            'error': f'您最多只能创建{quota.dh_limit}个数字人',
            'current': dh_count,
            'limit': quota.dh_limit,
            'message': '升级会员可创建更多数字人'
        }

    return True, None


def check_kb_size_limit(user_id, new_file_size):
    """
    检查知识库大小是否超限
    参数:
        user_id: 用户ID
        new_file_size: 新上传文件的大小(字节)
    返回: (是否可以上传, 错误信息)
    """
    quota = UserQuota.query.filter_by(user_id=user_id).first()
    if not quota:
        quota = UserQuota(user_id=user_id)
        db.session.add(quota)
        db.session.commit()

    # 计算当前知识库总大小
    kb_total_size = 0
    docs = db.session.query(KnowledgeDoc).join(
        DigitalHuman, KnowledgeDoc.dh_id == DigitalHuman.id
    ).filter(DigitalHuman.user_id == user_id).all()

    for doc in docs:
        if doc.file_size:
            kb_total_size += doc.file_size

    # 转换为MB
    current_size_mb = kb_total_size / (1024 * 1024)
    new_size_mb = new_file_size / (1024 * 1024)
    total_size_mb = current_size_mb + new_size_mb

    if total_size_mb > quota.kb_size_limit:
        return False, {
            'error': f'知识库容量不足',
            'current': round(current_size_mb, 2),
            'limit': quota.kb_size_limit,
            'fileSize': round(new_size_mb, 2),
            'message': f'升级会员可获得{quota.kb_size_limit * 10}MB知识库空间'
        }

    return True, None


def get_quota_usage(user_id):
    """
    获取用户配额使用情况
    返回: 配额使用详情字典
    """
    quota = UserQuota.query.filter_by(user_id=user_id).first()
    if not quota:
        quota = UserQuota(user_id=user_id)
        db.session.add(quota)
        db.session.commit()

    # 重置每日配额
    quota.reset_daily_quota()
    db.session.commit()

    # 统计当前使用
    dh_count = DigitalHuman.query.filter_by(user_id=user_id).count()

    # 计算知识库总大小
    kb_total_size = 0
    docs = db.session.query(KnowledgeDoc).join(
        DigitalHuman, KnowledgeDoc.dh_id == DigitalHuman.id
    ).filter(DigitalHuman.user_id == user_id).all()

    for doc in docs:
        if doc.file_size:
            kb_total_size += doc.file_size

    kb_total_size_mb = round(kb_total_size / (1024 * 1024), 2)

    return {
        'quota': quota.to_dict(),
        'usage': {
            'dhCount': dh_count,
            'dhLimit': quota.dh_limit,
            'dhPercent': round((dh_count / quota.dh_limit) * 100, 1) if quota.dh_limit > 0 else 0,

            'kbSizeMB': kb_total_size_mb,
            'kbSizeLimit': quota.kb_size_limit,
            'kbPercent': round((kb_total_size_mb / quota.kb_size_limit) * 100, 1) if quota.kb_size_limit > 0 else 0,

            'dailyChatUsed': quota.daily_chat_used,
            'dailyChatLimit': quota.daily_chat_limit,
            'dailyChatPercent': round((quota.daily_chat_used / quota.daily_chat_limit) * 100, 1) if quota.daily_chat_limit > 0 else 0,

            'dailyVoiceUsed': quota.daily_voice_used,
            'dailyVoiceLimit': quota.daily_voice_limit,
            'dailyVoicePercent': round((quota.daily_voice_used / quota.daily_voice_limit) * 100, 1) if quota.daily_voice_limit > 0 else 0
        }
    }
