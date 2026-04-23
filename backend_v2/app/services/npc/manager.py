"""
MindPal Backend V2 - NPC Manager
管理NPC人设和对话生成
"""

from typing import Dict, List, Optional
from pathlib import Path
import yaml


class NPCConfig:
    """NPC配置数据"""

    def __init__(self, config_data: dict):
        self.name = config_data.get("name", "")
        self.english_name = config_data.get("english_name", "")
        self.role = config_data.get("role", "")
        self.base_prompt = config_data.get("base_prompt", "")
        self.affinity_levels = config_data.get("affinity_levels", {})
        self.emotion_responses = config_data.get("emotion_responses", {})
        self.crisis_responses = config_data.get("crisis_responses", {})
        self.quest_dialogues = config_data.get("quest_dialogues", {})

    def get_affinity_style(self, affinity_value: int) -> dict:
        """根据好感度获取对话风格"""
        for level, config in self.affinity_levels.items():
            range_min, range_max = config.get("range", [0, 100])
            if range_min <= affinity_value <= range_max:
                return config
        # 默认返回第一级
        return self.affinity_levels.get(1, {})

    def build_system_prompt(
        self,
        affinity_value: int = 0,
        player_name: str = "旅人",
        memories: List[str] = None,
    ) -> str:
        """
        构建完整的System Prompt

        Args:
            affinity_value: 当前好感度
            player_name: 玩家昵称
            memories: 相关记忆片段

        Returns:
            完整的System Prompt
        """
        affinity_config = self.get_affinity_style(affinity_value)

        prompt_parts = [
            self.base_prompt,
            f"\n【当前关系】",
            f"- 好感度等级: {affinity_config.get('title', '初识')}",
            f"- 对话风格: {affinity_config.get('style', '友善')}",
            f"- 对方称呼: {player_name}",
        ]

        # 添加相关记忆
        if memories:
            prompt_parts.append("\n【相关记忆】")
            for memory in memories[:5]:  # 最多5条记忆
                prompt_parts.append(f"- {memory}")

        # 添加输出格式要求
        prompt_parts.append("\n【输出要求】")
        prompt_parts.append("- 回复长度适中，一般不超过100字")
        prompt_parts.append("- 保持角色一致性")
        prompt_parts.append("- 自然地融入情感和性格特点")

        return "\n".join(prompt_parts)


class NPCManager:
    """NPC管理器"""

    def __init__(self):
        self._configs: Dict[str, NPCConfig] = {}
        self._prompts_dir = Path(__file__).parent / "prompts"
        self._load_all_configs()

    def _load_all_configs(self):
        """加载所有NPC配置"""
        if not self._prompts_dir.exists():
            return

        for yaml_file in self._prompts_dir.glob("*.yaml"):
            npc_id = yaml_file.stem
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)
                    self._configs[npc_id] = NPCConfig(config_data)
            except Exception as e:
                print(f"[NPCManager] 加载配置失败 {npc_id}: {e}")

    def get_config(self, npc_id: str) -> Optional[NPCConfig]:
        """获取NPC配置"""
        return self._configs.get(npc_id)

    def get_all_npc_ids(self) -> List[str]:
        """获取所有NPC ID"""
        return list(self._configs.keys())

    def build_prompt_for_npc(
        self,
        npc_id: str,
        affinity_value: int = 0,
        player_name: str = "旅人",
        memories: List[str] = None,
    ) -> str:
        """
        为指定NPC构建System Prompt

        Args:
            npc_id: NPC ID
            affinity_value: 好感度值
            player_name: 玩家名称
            memories: 相关记忆

        Returns:
            System Prompt字符串
        """
        config = self.get_config(npc_id)
        if not config:
            # 返回默认提示
            return f"你是{npc_id}，一个友善的NPC。请根据玩家的消息进行回复。"

        return config.build_system_prompt(
            affinity_value=affinity_value,
            player_name=player_name,
            memories=memories,
        )

    def get_emotion_response(
        self,
        npc_id: str,
        emotion: str
    ) -> Optional[str]:
        """
        获取NPC对特定情绪的响应模板

        Args:
            npc_id: NPC ID
            emotion: 情绪类型

        Returns:
            响应模板或None
        """
        config = self.get_config(npc_id)
        if not config:
            return None

        responses = config.emotion_responses.get(emotion, [])
        if responses:
            import random
            return random.choice(responses)
        return None


# 全局单例
_npc_manager: Optional[NPCManager] = None


def get_npc_manager() -> NPCManager:
    """获取NPC管理器单例"""
    global _npc_manager
    if _npc_manager is None:
        _npc_manager = NPCManager()
    return _npc_manager
