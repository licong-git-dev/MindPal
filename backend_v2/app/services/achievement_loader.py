"""
MindPal Backend V2 - Achievement Data Loader
成就数据加载器
"""

import os
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path


class AchievementLoader:
    """成就配置加载器"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # 默认路径
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "data" / "achievements.yaml"
        self.config_path = Path(config_path)
        self._achievements: List[Dict[str, Any]] = []
        self._loaded = False

    def load(self) -> List[Dict[str, Any]]:
        """加载成就配置"""
        if self._loaded:
            return self._achievements

        if not self.config_path.exists():
            print(f"Warning: Achievement config not found at {self.config_path}")
            return []

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self._achievements = data.get('achievements', [])
                self._loaded = True
                return self._achievements
        except Exception as e:
            print(f"Error loading achievements: {e}")
            return []

    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有成就"""
        if not self._loaded:
            self.load()
        return self._achievements

    def get_by_id(self, achievement_id: str) -> Optional[Dict[str, Any]]:
        """通过ID获取成就"""
        if not self._loaded:
            self.load()
        for ach in self._achievements:
            if ach.get('id') == achievement_id:
                return ach
        return None

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """通过分类获取成就"""
        if not self._loaded:
            self.load()
        return [ach for ach in self._achievements if ach.get('category') == category]

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        if not self._loaded:
            self.load()
        categories = set()
        for ach in self._achievements:
            if 'category' in ach:
                categories.add(ach['category'])
        return list(categories)


# 单例
_loader: Optional[AchievementLoader] = None


def get_achievement_loader() -> AchievementLoader:
    """获取成就加载器实例"""
    global _loader
    if _loader is None:
        _loader = AchievementLoader()
    return _loader


async def seed_achievements(db) -> int:
    """
    将配置文件中的成就写入数据库

    Returns:
        int: 新增的成就数量
    """
    from sqlalchemy import select
    from app.models import Achievement

    loader = get_achievement_loader()
    achievements = loader.get_all()

    if not achievements:
        return 0

    # 获取已存在的成就ID
    stmt = select(Achievement.id)
    result = await db.execute(stmt)
    existing_ids = {row[0] for row in result.fetchall()}

    count = 0
    for ach_data in achievements:
        if ach_data['id'] in existing_ids:
            continue

        # 处理rewards
        rewards = ach_data.get('rewards', {})
        if isinstance(rewards, dict):
            # 转换items格式
            if 'items' in rewards:
                rewards['items'] = [
                    {"id": item['id'], "count": item.get('count', 1)}
                    for item in rewards['items']
                ]

        achievement = Achievement(
            id=ach_data['id'],
            name=ach_data['name'],
            description=ach_data['description'],
            category=ach_data.get('category', 'general'),
            points=ach_data.get('points', 10),
            icon=ach_data.get('icon', 'default'),
            is_hidden=ach_data.get('is_hidden', False),
            target_value=ach_data.get('target_value', 1),
            rewards=rewards
        )
        db.add(achievement)
        count += 1

    # 不在这里commit，由调用方决定
    return count
