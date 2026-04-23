"""
MindPal Backend V2 - Emotion Analyzer
情感分析器 - 关键词检测 + LLM增强分析
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class EmotionType(str, Enum):
    """情感类型"""
    JOY = "joy"           # 快乐
    SADNESS = "sadness"   # 悲伤
    ANGER = "anger"       # 愤怒
    FEAR = "fear"         # 恐惧
    SURPRISE = "surprise" # 惊讶
    DISGUST = "disgust"   # 厌恶
    NEUTRAL = "neutral"   # 中性


@dataclass
class EmotionResult:
    """情感分析结果"""
    dominant: EmotionType              # 主导情感
    scores: Dict[str, float]           # 各情感得分
    intensity: float                   # 强度 0-1
    needs_comfort: bool                # 是否需要安慰
    is_positive: bool                  # 是否积极情感
    crisis_risk: bool = False          # 是否有危机风险
    keywords_matched: List[str] = field(default_factory=list)  # 匹配的关键词


class EmotionAnalyzer:
    """多模态情感分析器"""

    # 情感关键词库
    EMOTION_KEYWORDS: Dict[str, List[str]] = {
        EmotionType.JOY: [
            "开心", "高兴", "快乐", "幸福", "棒", "太好了", "哈哈", "嘻嘻",
            "爱", "喜欢", "感谢", "谢谢", "好开心", "太棒了", "超级开心",
            "兴奋", "期待", "美好", "温暖", "舒服", "满意", "完美", "赞",
            "nice", "great", "happy", "love", "好耶", "耶", "嘿嘿"
        ],
        EmotionType.SADNESS: [
            "难过", "伤心", "悲伤", "哭", "痛苦", "失望", "孤独", "寂寞",
            "累了", "好累", "心累", "疲惫", "无聊", "没意思", "烦", "郁闷",
            "沮丧", "低落", "失落", "空虚", "绝望", "无助", "心痛", "难受",
            "呜呜", "555", "😢", "😭", "想哭", "流泪", "心碎"
        ],
        EmotionType.ANGER: [
            "生气", "愤怒", "烦死了", "气死了", "讨厌", "恨", "混蛋", "滚",
            "烦人", "恼火", "不爽", "火大", "可恶", "该死", "去死", "傻逼",
            "艹", "cao", "草", "tmd", "妈的", "操", "靠", "fuck"
        ],
        EmotionType.FEAR: [
            "害怕", "担心", "焦虑", "恐惧", "紧张", "不安", "慌", "怕",
            "忐忑", "恐慌", "惶恐", "战战兢兢", "胆战心惊", "心慌", "心虚",
            "压力大", "压力", "崩溃", "受不了", "撑不住", "快疯了"
        ],
        EmotionType.SURPRISE: [
            "惊讶", "意外", "没想到", "天哪", "哇", "不敢相信", "震惊",
            "居然", "竟然", "原来", "啊", "哦", "噢", "咦", "诶",
            "真的吗", "不会吧", "what", "OMG", "天呐"
        ],
        EmotionType.DISGUST: [
            "恶心", "讨厌", "厌恶", "反感", "无语", "呵呵", "切", "呸",
            "鄙视", "看不起", "受够了", "够了", "烦透了"
        ]
    }

    # 危机关键词（需要特别关注）
    CRISIS_KEYWORDS: List[str] = [
        "不想活", "自杀", "结束生命", "活着没意思", "死", "去死",
        "伤害自己", "割", "跳楼", "跳下去", "离开这个世界",
        "没有意义", "活不下去", "不想醒来", "消失", "解脱",
        "一了百了", "永远离开", "不想活了", "活着好累"
    ]

    # 情感强度修饰词
    INTENSITY_MODIFIERS: Dict[str, float] = {
        "非常": 1.5, "特别": 1.5, "超级": 1.6, "太": 1.4,
        "好": 1.2, "很": 1.3, "真的": 1.2, "真": 1.2,
        "有点": 0.7, "稍微": 0.6, "略微": 0.5
    }

    def __init__(self, enable_llm: bool = False):
        """
        Args:
            enable_llm: 是否启用LLM增强分析（需要更多计算资源）
        """
        self.enable_llm = enable_llm

    def analyze(self, text: str) -> EmotionResult:
        """分析文本情感"""
        # 1. 关键词检测
        scores, matched_keywords = self._keyword_detection(text)

        # 2. 计算强度
        intensity = self._calculate_intensity(text, scores)

        # 3. 危机检测
        crisis_risk = self._detect_crisis(text)

        # 4. 确定主导情感
        dominant = self._get_dominant_emotion(scores)

        # 5. 判断是否需要安慰
        needs_comfort = (
            scores.get(EmotionType.SADNESS, 0) > 0.3 or
            scores.get(EmotionType.FEAR, 0) > 0.3 or
            crisis_risk
        )

        # 6. 判断是否积极
        is_positive = dominant in [EmotionType.JOY, EmotionType.SURPRISE]

        return EmotionResult(
            dominant=dominant,
            scores={k.value: v for k, v in scores.items()},
            intensity=min(intensity, 1.0),
            needs_comfort=needs_comfort,
            is_positive=is_positive,
            crisis_risk=crisis_risk,
            keywords_matched=matched_keywords
        )

    def _keyword_detection(self, text: str) -> Tuple[Dict[EmotionType, float], List[str]]:
        """关键词检测"""
        text_lower = text.lower()
        scores: Dict[EmotionType, float] = {e: 0.0 for e in EmotionType}
        matched_keywords: List[str] = []

        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    # 基础分数
                    base_score = 0.3

                    # 检查强度修饰词
                    for modifier, multiplier in self.INTENSITY_MODIFIERS.items():
                        if modifier in text_lower:
                            keyword_idx = text_lower.find(keyword.lower())
                            modifier_idx = text_lower.find(modifier)
                            # 修饰词在关键词前10个字符内
                            if 0 <= keyword_idx - modifier_idx <= 10:
                                base_score *= multiplier
                                break

                    scores[emotion] += base_score
                    matched_keywords.append(keyword)

        # 归一化
        total = sum(scores.values())
        if total > 0:
            scores = {e: s / total for e, s in scores.items()}
        else:
            scores[EmotionType.NEUTRAL] = 1.0

        return scores, matched_keywords

    def _calculate_intensity(
        self,
        text: str,
        scores: Dict[EmotionType, float]
    ) -> float:
        """计算情感强度"""
        # 基础强度：最高情感分数
        base_intensity = max(scores.values())

        # 修饰词加成
        intensity_boost = 0.0
        for modifier, multiplier in self.INTENSITY_MODIFIERS.items():
            if modifier in text:
                intensity_boost = max(intensity_boost, multiplier - 1.0)

        # 标点符号加成
        exclamation_count = text.count("!") + text.count("！")
        question_count = text.count("?") + text.count("？")
        intensity_boost += exclamation_count * 0.1
        intensity_boost += question_count * 0.05

        # 重复字符加成（如"啊啊啊"）
        repeat_pattern = re.compile(r'(.)\1{2,}')
        if repeat_pattern.search(text):
            intensity_boost += 0.2

        # emoji加成
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+",
            flags=re.UNICODE
        )
        if emoji_pattern.search(text):
            intensity_boost += 0.15

        return min(base_intensity + intensity_boost, 1.0)

    def _detect_crisis(self, text: str) -> bool:
        """检测危机关键词"""
        text_lower = text.lower()
        for keyword in self.CRISIS_KEYWORDS:
            if keyword in text_lower:
                return True
        return False

    def _get_dominant_emotion(
        self,
        scores: Dict[EmotionType, float]
    ) -> EmotionType:
        """获取主导情感"""
        if not scores or all(v == 0 for v in scores.values()):
            return EmotionType.NEUTRAL

        return max(scores, key=scores.get)

    def get_response_instruction(self, result: EmotionResult) -> str:
        """根据情感分析结果生成回复指导"""
        instructions = {
            EmotionType.JOY: """
## 情感回应指导
用户心情不错！请：
- 回应用户的积极情绪，分享快乐
- 可以适当活泼、开玩笑
- 鼓励用户继续保持好心情
- 语气可以轻松愉快
""",
            EmotionType.SADNESS: """
## 情感回应指导
用户正在经历悲伤情绪。请：
- 首先表达理解和共情，不要急于给建议
- 使用温柔、包容的语气
- 适当询问发生了什么，但不要追问
- 在适当时候轻轻引导看到希望
- 让用户感到被理解和接纳
""",
            EmotionType.ANGER: """
## 情感回应指导
用户有些愤怒或烦躁。请：
- 先认可用户的感受，表示理解
- 不要否定或试图立刻讲道理
- 给用户发泄的空间
- 用冷静但不冷漠的语气回应
- 适时转移注意力到轻松话题
""",
            EmotionType.FEAR: """
## 情感回应指导
用户表现出担忧或恐惧。请：
- 提供安全感和陪伴感
- 用稳定、可靠的语气说话
- 帮助用户理清思路
- 提供具体可行的建议
- 强调会陪伴在身边
""",
            EmotionType.SURPRISE: """
## 情感回应指导
用户感到惊讶。请：
- 回应用户的反应
- 可以表现出好奇
- 帮助用户理解情况
""",
            EmotionType.DISGUST: """
## 情感回应指导
用户表现出厌恶或反感。请：
- 理解用户的感受
- 不要强迫用户接受
- 尊重用户的边界
""",
            EmotionType.NEUTRAL: """
## 情感回应指导
用户情绪平稳。请：
- 正常对话即可
- 保持友好和自然
"""
        }

        instruction = instructions.get(result.dominant, instructions[EmotionType.NEUTRAL])

        # 如果需要安慰，添加额外指导
        if result.needs_comfort and result.dominant != EmotionType.SADNESS:
            instruction += """
### 额外提示
用户可能需要一些安慰和支持，请在回复中体现关心。
"""

        # 添加强度信息
        if result.intensity > 0.7:
            instruction += f"""
### 情感强度
用户情绪较为强烈（强度: {result.intensity:.0%}），请给予更多关注。
"""

        return instruction


# 单例实例
_analyzer: Optional[EmotionAnalyzer] = None


def get_emotion_analyzer() -> EmotionAnalyzer:
    """获取情感分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = EmotionAnalyzer()
    return _analyzer
