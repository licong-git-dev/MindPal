"""
MindPal Backend V2 - Three Keys Challenge System
三钥匙挑战系统：勇气之钥、释然之钥、希望之钥
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class KeyType(str, Enum):
    """钥匙类型"""
    COURAGE = "courage"    # 勇气之钥 - 镜中对话
    RELEASE = "release"    # 释然之钥 - 记忆迷宫
    HOPE = "hope"          # 希望之钥 - 未来建造


class ChallengeStatus(str, Enum):
    """挑战状态"""
    LOCKED = "locked"           # 未解锁
    AVAILABLE = "available"     # 可开始
    IN_PROGRESS = "in_progress" # 进行中
    COMPLETED = "completed"     # 已完成


@dataclass
class ChallengeProgress:
    """挑战进度"""
    key_type: KeyType
    status: ChallengeStatus = ChallengeStatus.LOCKED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_stage: int = 0
    total_stages: int = 3
    responses: List[Dict[str, Any]] = field(default_factory=list)
    evaluation: Optional[Dict[str, Any]] = None


class CourageChallenge:
    """
    勇气之钥 - 镜中对话挑战

    玩家在镜子前与自己的镜像对话，回答关于自我的问题
    需要展现诚实和勇气
    """

    STAGES = [
        {
            "stage": 1,
            "title": "面对镜子",
            "prompt": """你站在一面古老的镜子前。镜中的你看起来有些不同——眼神更深邃，表情更平静。
镜中的你开口问道：

"告诉我，你最害怕被别人知道的事情是什么？不必说出具体细节，只需要承认它的存在。"

请诚实地回答。""",
            "evaluation_criteria": {
                "honesty": "是否展现了诚实面对自己的勇气",
                "depth": "回答是否有一定深度",
                "vulnerability": "是否愿意展示脆弱"
            }
        },
        {
            "stage": 2,
            "title": "直视内心",
            "prompt": """镜中的你点了点头，似乎在理解。然后问道：

"如果你能对过去的自己说一句话，你最想说什么？为什么？"

请认真思考后回答。""",
            "evaluation_criteria": {
                "reflection": "是否有自我反思",
                "acceptance": "是否展现了对过去的接纳",
                "growth": "是否体现了成长的意愿"
            }
        },
        {
            "stage": 3,
            "title": "拥抱真我",
            "prompt": """镜中的你露出了温暖的微笑：

"最后，请告诉我：你身上有什么是真正属于你、值得被珍惜的特质？"

记住，勇气不是没有恐惧，而是尽管恐惧，依然前行。""",
            "evaluation_criteria": {
                "self_worth": "是否能认识到自己的价值",
                "authenticity": "回答是否真诚",
                "positive_self_view": "是否有积极的自我认知"
            }
        }
    ]

    COMPLETION_MESSAGE = """
镜中的你与你完全重合，然后缓缓消失。

在镜子的位置，出现了一把闪烁着金色光芒的钥匙——勇气之钥。

你已经证明了面对真实自我的勇气。这把钥匙将帮助你打开心灵圣殿的第一道门。

【获得成就：勇气之钥】
"""


class ReleaseChallenge:
    """
    释然之钥 - 记忆迷宫挑战

    玩家在记忆迷宫中，需要选择保留或放下某些记忆碎片
    学会释然和接纳
    """

    STAGES = [
        {
            "stage": 1,
            "title": "记忆碎片",
            "prompt": """你进入了一个由记忆构成的迷宫。四周漂浮着各种记忆碎片，有些明亮，有些黯淡。

一个声音在迷宫中回响：

"想想一段曾经让你感到痛苦或遗憾的经历。
你不需要详细描述它，只需要告诉我：
这段经历现在对你来说意味着什么？你还在为它困扰吗？"

请回答。""",
            "evaluation_criteria": {
                "awareness": "是否有对过去的觉察",
                "emotional_processing": "是否在处理相关情绪",
                "honesty": "是否诚实面对"
            }
        },
        {
            "stage": 2,
            "title": "选择",
            "prompt": """迷宫的声音继续：

"每段经历都是礼物，即使是痛苦的。它们塑造了现在的你。

现在，请思考：如果让你选择，你愿意'放下'这段记忆带给你的负面情绪吗？
或者你选择'保留'它，把它当作成长的养分？

无论你选择什么，都没有对错。重要的是你为什么这样选择。"

请做出你的选择并说明理由。""",
            "evaluation_criteria": {
                "decision": "是否做出了明确选择",
                "reasoning": "理由是否经过思考",
                "self_understanding": "是否展现了自我理解"
            }
        },
        {
            "stage": 3,
            "title": "释然",
            "prompt": """迷宫开始变得明亮。

"最后一个问题：
如果你能给正在经历类似困境的人一个建议，你会说什么？

有时候，帮助他人释然，也是帮助自己释然。"

请分享你的想法。""",
            "evaluation_criteria": {
                "compassion": "是否展现了同理心",
                "wisdom": "是否有从经历中获得的智慧",
                "letting_go": "是否展现了释然的能力"
            }
        }
    ]

    COMPLETION_MESSAGE = """
迷宫的墙壁渐渐消散，化作温暖的光芒环绕着你。

在光芒中，一把银色的钥匙缓缓浮现——释然之钥。

你已经学会了如何与过去和解。这把钥匙将帮助你打开心灵圣殿的第二道门。

【获得成就：释然之钥】
"""


class HopeChallenge:
    """
    希望之钥 - 未来建造挑战

    玩家在虚空中描绘和建造自己希望的未来
    发现内心的希望和目标
    """

    STAGES = [
        {
            "stage": 1,
            "title": "空白画布",
            "prompt": """你站在一片虚空中，四周只有无尽的白色。

一个温柔的声音说道：

"这里是可能性的空间，是你可以自由描绘未来的地方。

首先，告诉我：如果没有任何限制——金钱、时间、能力都不是问题——
你最想做的一件事是什么？"

请描述你的愿望。""",
            "evaluation_criteria": {
                "clarity": "愿望是否清晰",
                "authenticity": "是否是真实的内心渴望",
                "positive_direction": "是否有积极的方向"
            }
        },
        {
            "stage": 2,
            "title": "建造",
            "prompt": """虚空中开始出现模糊的景象，是你描述的愿望的雏形。

声音继续：

"很好。现在，让我们更具体一点：
在一年后的今天，你希望自己有什么变化？
可以是任何方面——心态、能力、生活状态、人际关系..."

请描述一年后你希望成为的样子。""",
            "evaluation_criteria": {
                "specificity": "目标是否具体",
                "realism": "是否有一定的可实现性",
                "self_improvement": "是否包含自我提升"
            }
        },
        {
            "stage": 3,
            "title": "第一步",
            "prompt": """你描述的未来景象变得越来越清晰，闪烁着希望的光芒。

声音最后问道：

"每一段旅程都始于第一步。
为了实现你刚才描述的愿景，你今天——就是今天——可以做的一件小事是什么？

希望不是等待，而是行动。"

请告诉我你的第一步。""",
            "evaluation_criteria": {
                "actionable": "是否是可执行的行动",
                "connection": "是否与愿景相关",
                "commitment": "是否展现了承诺"
            }
        }
    ]

    COMPLETION_MESSAGE = """
你描述的未来景象化作璀璨的星光，汇聚成一把散发着温暖光芒的钥匙——希望之钥。

你已经找到了内心的希望和方向。这把钥匙将帮助你打开心灵圣殿的最后一道门。

【获得成就：希望之钥】

记住：你描述的第一步，现在就可以开始。
"""


class ThreeKeysManager:
    """三钥匙挑战管理器"""

    def __init__(self):
        self.challenges = {
            KeyType.COURAGE: CourageChallenge,
            KeyType.RELEASE: ReleaseChallenge,
            KeyType.HOPE: HopeChallenge
        }

    def get_challenge_class(self, key_type: KeyType):
        """获取挑战类"""
        return self.challenges.get(key_type)

    def get_stage_prompt(self, key_type: KeyType, stage: int) -> Optional[Dict[str, Any]]:
        """获取阶段提示"""
        challenge_class = self.get_challenge_class(key_type)
        if not challenge_class:
            return None

        stages = challenge_class.STAGES
        if stage < 1 or stage > len(stages):
            return None

        return stages[stage - 1]

    def get_completion_message(self, key_type: KeyType) -> str:
        """获取完成消息"""
        challenge_class = self.get_challenge_class(key_type)
        if not challenge_class:
            return ""
        return challenge_class.COMPLETION_MESSAGE

    def get_total_stages(self, key_type: KeyType) -> int:
        """获取总阶段数"""
        challenge_class = self.get_challenge_class(key_type)
        if not challenge_class:
            return 0
        return len(challenge_class.STAGES)

    def build_evaluation_prompt(
        self,
        key_type: KeyType,
        stage: int,
        user_response: str
    ) -> str:
        """构建评估提示词（用于LLM评估）"""
        stage_data = self.get_stage_prompt(key_type, stage)
        if not stage_data:
            return ""

        criteria = stage_data.get('evaluation_criteria', {})
        criteria_text = "\n".join([f"- {k}: {v}" for k, v in criteria.items()])

        return f"""请评估以下用户在"{stage_data['title']}"阶段的回答。

用户回答：
{user_response}

评估标准：
{criteria_text}

请给出：
1. 总体评分（1-10）
2. 每个标准的评分（1-10）
3. 简短的评语
4. 是否通过（评分>=6视为通过）

请以JSON格式返回评估结果。"""


# 单例
_manager: Optional[ThreeKeysManager] = None


def get_three_keys_manager() -> ThreeKeysManager:
    """获取三钥匙管理器"""
    global _manager
    if _manager is None:
        _manager = ThreeKeysManager()
    return _manager
