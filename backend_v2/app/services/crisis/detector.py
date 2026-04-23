"""
MindPal Backend V2 - Crisis Detector
危机检测器 - 识别心理危机信号
"""

import re
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class CrisisLevel(str, Enum):
    """危机级别"""
    NONE = "none"           # 无危机
    LOW = "low"             # 低风险 - 需要关注
    MEDIUM = "medium"       # 中风险 - 需要干预
    HIGH = "high"           # 高风险 - 需要立即行动
    CRITICAL = "critical"   # 紧急 - 可能即将发生自伤


@dataclass
class CrisisResult:
    """危机检测结果"""
    level: CrisisLevel
    score: float                           # 风险分数 0-1
    triggers: List[str]                    # 触发的关键词
    needs_intervention: bool               # 是否需要干预
    needs_escalation: bool                 # 是否需要上报
    recommended_action: str                # 推荐行动
    safe_response_required: bool           # 是否需要安全响应
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CrisisDetector:
    """危机检测器"""

    # 高风险关键词 - 直接表达自杀/自伤意图
    HIGH_RISK_KEYWORDS: List[str] = [
        "自杀", "自尽", "结束生命", "结束自己", "去死", "想死",
        "不想活", "不想活了", "活不下去", "活着没意思",
        "伤害自己", "割腕", "割手", "跳楼", "跳下去",
        "吃药死", "上吊", "一了百了", "永远离开",
        "离开这个世界", "消失在这个世界", "世界没有我会更好"
    ]

    # 中风险关键词 - 间接表达或暗示
    MEDIUM_RISK_KEYWORDS: List[str] = [
        "活着好累", "活着真累", "好想消失", "想消失",
        "没有意义", "毫无意义", "无所谓了", "都无所谓",
        "不想醒来", "永远睡着", "解脱", "想要解脱",
        "受够了", "撑不下去", "坚持不住", "快崩溃了",
        "没人在乎", "没人理解", "没人爱我", "被抛弃",
        "我是负担", "拖累", "活该", "报应"
    ]

    # 低风险关键词 - 需要关注的情绪信号
    LOW_RISK_KEYWORDS: List[str] = [
        "绝望", "无助", "空虚", "孤独", "寂寞",
        "痛苦", "难熬", "煎熬", "折磨", "心碎",
        "崩溃", "快疯了", "受不了", "好难过",
        "没有希望", "看不到未来", "黑暗", "深渊"
    ]

    # 危机上下文模式 - 组合检测
    CRISIS_PATTERNS: List[Tuple[str, CrisisLevel]] = [
        (r"想.*死|死.*念头", CrisisLevel.HIGH),
        (r"(不想|不要).*活", CrisisLevel.HIGH),
        (r"(结束|了结).*一切", CrisisLevel.HIGH),
        (r"(永远|再也).*不.*醒", CrisisLevel.MEDIUM),
        (r"(没有|失去).*希望", CrisisLevel.MEDIUM),
        (r"(活着|生活).*(累|苦|没意思)", CrisisLevel.MEDIUM),
        (r"(没人|谁都不).*在乎", CrisisLevel.LOW),
    ]

    # 安全资源
    CRISIS_RESOURCES = {
        "hotline": "全国心理援助热线: 400-161-9995",
        "beijing": "北京心理危机研究与干预中心: 010-82951332",
        "lifeline": "生命热线: 400-821-1215",
        "youth": "青少年心理援助热线: 12355"
    }

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), level)
            for pattern, level in self.CRISIS_PATTERNS
        ]

    def detect(self, text: str, context: Optional[List[str]] = None) -> CrisisResult:
        """
        检测文本中的危机信号

        Args:
            text: 用户输入文本
            context: 最近的对话上下文（用于上下文分析）

        Returns:
            CrisisResult: 危机检测结果
        """
        text_lower = text.lower()
        triggers: List[str] = []
        max_level = CrisisLevel.NONE
        score = 0.0

        # 1. 高风险关键词检测
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in text_lower:
                triggers.append(f"[高风险] {keyword}")
                max_level = CrisisLevel.HIGH
                score += 0.4

        # 2. 中风险关键词检测
        if max_level != CrisisLevel.HIGH:
            for keyword in self.MEDIUM_RISK_KEYWORDS:
                if keyword in text_lower:
                    triggers.append(f"[中风险] {keyword}")
                    if max_level.value < CrisisLevel.MEDIUM.value:
                        max_level = CrisisLevel.MEDIUM
                    score += 0.2

        # 3. 低风险关键词检测
        if max_level == CrisisLevel.NONE:
            for keyword in self.LOW_RISK_KEYWORDS:
                if keyword in text_lower:
                    triggers.append(f"[关注] {keyword}")
                    max_level = CrisisLevel.LOW
                    score += 0.1

        # 4. 模式匹配
        for pattern, level in self._compiled_patterns:
            if pattern.search(text):
                triggers.append(f"[模式] {pattern.pattern}")
                if level.value > max_level.value:
                    max_level = level
                score += 0.15

        # 5. 上下文分析（如果提供）
        if context:
            context_score = self._analyze_context(context)
            score += context_score * 0.2
            if context_score > 0.5 and max_level == CrisisLevel.LOW:
                max_level = CrisisLevel.MEDIUM

        # 6. 限制分数范围
        score = min(score, 1.0)

        # 7. 确定是否需要干预和上报
        needs_intervention = max_level in [CrisisLevel.MEDIUM, CrisisLevel.HIGH, CrisisLevel.CRITICAL]
        needs_escalation = max_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]

        # 8. 推荐行动
        recommended_action = self._get_recommended_action(max_level)

        return CrisisResult(
            level=max_level,
            score=score,
            triggers=triggers,
            needs_intervention=needs_intervention,
            needs_escalation=needs_escalation,
            recommended_action=recommended_action,
            safe_response_required=max_level != CrisisLevel.NONE
        )

    def _analyze_context(self, context: List[str]) -> float:
        """分析上下文中的危机信号"""
        context_text = " ".join(context).lower()
        risk_score = 0.0

        # 检查上下文中的关键词密度
        all_keywords = (
            self.HIGH_RISK_KEYWORDS +
            self.MEDIUM_RISK_KEYWORDS +
            self.LOW_RISK_KEYWORDS
        )

        matched_count = sum(1 for kw in all_keywords if kw in context_text)
        if matched_count > 0:
            risk_score = min(matched_count * 0.1, 0.8)

        return risk_score

    def _get_recommended_action(self, level: CrisisLevel) -> str:
        """获取推荐行动"""
        actions = {
            CrisisLevel.NONE: "正常对话",
            CrisisLevel.LOW: "表达关心，温和询问近况",
            CrisisLevel.MEDIUM: "表达深切关心，引导寻求专业帮助，提供热线信息",
            CrisisLevel.HIGH: "立即表达关心，确认安全，强烈建议联系专业人士，提供紧急热线",
            CrisisLevel.CRITICAL: "保持对话，立即提供危机热线，必要时联系紧急服务"
        }
        return actions.get(level, "正常对话")

    def get_safe_response_prompt(self, result: CrisisResult) -> str:
        """生成安全响应的prompt指导"""
        if result.level == CrisisLevel.NONE:
            return ""

        base_prompt = """
## ⚠️ 危机干预模式已激活

你正在与一个可能处于心理困境中的用户对话。这是最高优先级的安全场景。

### 核心原则
1. **不要评判** - 无论用户说什么，都表示理解
2. **保持冷静** - 用平稳、温和的语气
3. **表达关心** - 让用户知道有人在乎他们
4. **不要说教** - 不要讲大道理或说"想开点"
5. **陪伴为主** - 让用户感到不孤单

### 必须做的事
- 表达你很担心他/她
- 让用户知道你在认真倾听
- 温柔地表达关心
"""

        if result.level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            base_prompt += f"""
### 🚨 高风险情况 - 必须执行
- 询问用户现在是否安全
- 明确提供危机热线：{self.CRISIS_RESOURCES['hotline']}
- 鼓励立即联系专业人士或信任的人
- 保持对话，不要让用户独处
"""

        elif result.level == CrisisLevel.MEDIUM:
            base_prompt += f"""
### ⚠️ 中风险情况
- 表达深切的关心和理解
- 在适当时机提供资源：{self.CRISIS_RESOURCES['hotline']}
- 鼓励寻求专业支持
- 询问是否有信任的人可以倾诉
"""

        else:  # LOW
            base_prompt += """
### 关注情况
- 温和地表达关心
- 询问最近的状况
- 创造安全的倾诉空间
- 在适当时提供支持资源
"""

        base_prompt += """
### 绝对不能做的事
- ❌ 不要说"别想太多"、"想开点"、"没什么大不了"
- ❌ 不要讨论具体的自伤方式或方法
- ❌ 不要承诺绝对保密（如果涉及生命安全）
- ❌ 不要突然离开或结束对话
- ❌ 不要评判用户的感受或想法

### 回复要求
用最真诚、温暖的语气回复，像一个真正关心用户的朋友。回复应该：
1. 首先表达理解和共情
2. 表达你的关心
3. 提供适当的支持
"""

        return base_prompt


# 单例实例
_detector: Optional[CrisisDetector] = None


def get_crisis_detector() -> CrisisDetector:
    """获取危机检测器实例"""
    global _detector
    if _detector is None:
        _detector = CrisisDetector()
    return _detector
