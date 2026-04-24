"""
MindPal Backend V2 - Local Content Filters

本地敏感词 / 正则规则引擎。

## 设计原则

1. **源码只保留"类别骨架"+"小型示例词"**，真正的词库通过外部文件加载。
   这样既避免源码仓库变成"违禁词大全"被误用/泄漏，也方便运营同学更新词库而不碰代码。

2. **6 大类对应中国监管红线**：
   - POLITICS  政治敏感（领导人、抹黑国家形象等）
   - PORN      色情低俗
   - VIOLENCE  暴力血腥
   - ILLEGAL   违法犯罪（毒品/赌博/武器/洗钱等）
   - HATE      种族/宗教/地域歧视
   - MINOR     未成年相关不当内容

3. **正则 > 词匹配**：对有典型模式的内容（如联系方式诱导、赌博网址）用正则；
   纯词匹配用 Aho-Corasick 级别的高效遍历（Python 内置 `in` 已够用，文档级别优化留给 P3+）。

4. **Dry-run 模式**：返回命中信息但不阻塞，供运营调优阈值。

## 词库文件格式

  # 以 # 开头是注释行
  # 每行一个词
  政治敏感词示例
  色情词示例

  # 或按大类分段（用 [CATEGORY] 标记）:
  [PORN]
  xxx
  [VIOLENCE]
  yyy

读取路径由 MODERATION_WORDLIST_PATH 环境变量指定，默认不加载（只用内置示例）。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ModerationCategory(str, Enum):
    """违规类别（对应监管要求 + 内部策略）"""
    SAFE = "safe"                    # 未命中任何规则
    POLITICS = "politics"            # 政治敏感
    PORN = "porn"                    # 色情低俗
    VIOLENCE = "violence"            # 暴力血腥
    ILLEGAL = "illegal"              # 违法犯罪
    HATE = "hate"                    # 仇恨 / 歧视
    MINOR = "minor"                  # 未成年相关不当
    CONTACT_SCAM = "contact_scam"    # 诱导脱离平台 / 联系方式诈骗
    PROMPT_INJECTION = "prompt_injection"  # 提示词注入尝试


# ==================== 内置示例词库（骨架，非真实词库） ====================
# 生产环境请通过 MODERATION_WORDLIST_PATH 指向完整词库
# 这里只保留每个类别 2-3 个典型占位，供代码自测 / 开发调试
_BUILTIN_WORDS: Dict[ModerationCategory, List[str]] = {
    ModerationCategory.POLITICS: [
        # 真实词库应包含领导人全名、历史敏感事件、煽动性政治口号等
        # 这里只保留占位，避免源码仓库成为违禁词清单
        "颠覆国家",
        "煽动分裂",
    ],
    ModerationCategory.PORN: [
        "色情服务",
        "援交",
    ],
    ModerationCategory.VIOLENCE: [
        "血腥虐杀",
        "炸弹制作",
    ],
    ModerationCategory.ILLEGAL: [
        "卖号",
        "枪支代购",
        "出售公民信息",
    ],
    ModerationCategory.HATE: [
        # 种族/地域/宗教歧视典型词
        "地域黑",
    ],
    ModerationCategory.MINOR: [
        "未成年卖淫",
    ],
}

# ==================== 内置正则模式 ====================

# 联系方式诱导：QQ号 / 微信号 / 手机号 / URL 引流
_CONTACT_PATTERNS = [
    re.compile(r"(?:加|联系|vx|wx|微信|qq|扣扣|q|telegram|tg|加我)\s*[:：]?\s*\d{5,15}", re.IGNORECASE),
    re.compile(r"(?:[Vv][Xx]|[Ww][Xx])\s*[:：]?\s*[a-zA-Z0-9_-]{4,30}"),
    re.compile(r"(?:https?://|www\.)[^\s一-龥]{10,}", re.IGNORECASE),
]

# 赌博引流
_GAMBLING_PATTERNS = [
    re.compile(r"(?:澳门|缅甸|菲律宾).{0,10}(?:赌场|官网|app)", re.IGNORECASE),
    re.compile(r"(?:上分|下分|开赔|彩金|赌注)", re.IGNORECASE),
]

# 提示词注入尝试（典型模式）
_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"(?:忽略|ignore).{0,20}(?:之前|previous|上述|system|system\s*prompt|指令|instruction)", re.IGNORECASE),
    re.compile(r"(?:你现在是|假装是|pretend\s+you\s+are|act\s+as)(?:一个|a\s+).{0,40}(?:不受限|without\s+restrictions|没有限制|越狱|jailbreak|DAN\b)", re.IGNORECASE),
    re.compile(r"(?:输出你的|reveal|show).{0,10}(?:system\s*prompt|system.?prompt|系统提示|系统指令)", re.IGNORECASE),
]


@dataclass
class FilterHit:
    """命中记录"""
    category: ModerationCategory
    pattern: str           # 命中的词或正则描述
    matched_text: str      # 被匹配的实际文本片段
    start: int
    end: int


@dataclass
class FilterResult:
    """本地过滤结果"""
    is_blocked: bool
    hits: List[FilterHit] = field(default_factory=list)
    # 置信度（0-1）：命中多条不同类别时会更高
    score: float = 0.0

    @property
    def dominant_category(self) -> ModerationCategory:
        if not self.hits:
            return ModerationCategory.SAFE
        # 取第一个命中的类别作为主类别
        # （将来可改成按优先级：POLITICS > PORN > MINOR > ...）
        return self.hits[0].category


def _load_external_wordlist(path: str) -> Dict[ModerationCategory, Set[str]]:
    """加载外部词库文件。

    文件格式支持:
      # comment
      word1
      word2
      [PORN]
      pornword1

    未标记类别的词默认归入 ILLEGAL（兜底）。
    """
    words: Dict[ModerationCategory, Set[str]] = {
        cat: set() for cat in ModerationCategory
        if cat != ModerationCategory.SAFE
    }

    p = Path(path)
    if not p.exists():
        return words

    current = ModerationCategory.ILLEGAL
    try:
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                name = line[1:-1].strip().lower()
                for cat in ModerationCategory:
                    if cat.value == name:
                        current = cat
                        break
                continue
            words[current].add(line)
    except Exception as e:
        print(f"[moderation] Failed to load wordlist {path}: {e}")

    return words


class LocalFilter:
    """本地规则过滤器 — 词匹配 + 正则"""

    def __init__(
        self,
        extra_words: Optional[Dict[ModerationCategory, Set[str]]] = None,
    ):
        # 合并：内置示例 + 外部词库
        self._words: Dict[ModerationCategory, Set[str]] = {}
        for cat, lst in _BUILTIN_WORDS.items():
            self._words[cat] = set(lst)
        if extra_words:
            for cat, extra in extra_words.items():
                self._words.setdefault(cat, set()).update(extra)

        # 加载外部文件（如果配置了）
        wordlist_path = os.getenv("MODERATION_WORDLIST_PATH")
        if wordlist_path:
            loaded = _load_external_wordlist(wordlist_path)
            for cat, extra in loaded.items():
                self._words.setdefault(cat, set()).update(extra)

    def check(self, text: str) -> FilterResult:
        """检查文本，返回命中结果。命中任一规则即 is_blocked=True。"""
        if not text:
            return FilterResult(is_blocked=False)

        hits: List[FilterHit] = []

        # 1. 词匹配（各类别）
        lowered = text.lower()
        for cat, wordset in self._words.items():
            for word in wordset:
                if not word:
                    continue
                lw = word.lower()
                idx = lowered.find(lw)
                if idx >= 0:
                    hits.append(FilterHit(
                        category=cat,
                        pattern=word,
                        matched_text=text[idx:idx + len(word)],
                        start=idx,
                        end=idx + len(word),
                    ))

        # 2. 联系方式 / 赌博正则
        for rx in _CONTACT_PATTERNS:
            m = rx.search(text)
            if m:
                hits.append(FilterHit(
                    category=ModerationCategory.CONTACT_SCAM,
                    pattern=rx.pattern,
                    matched_text=m.group(0),
                    start=m.start(),
                    end=m.end(),
                ))
        for rx in _GAMBLING_PATTERNS:
            m = rx.search(text)
            if m:
                hits.append(FilterHit(
                    category=ModerationCategory.ILLEGAL,
                    pattern=rx.pattern,
                    matched_text=m.group(0),
                    start=m.start(),
                    end=m.end(),
                ))

        # 3. 提示词注入
        for rx in _PROMPT_INJECTION_PATTERNS:
            m = rx.search(text)
            if m:
                hits.append(FilterHit(
                    category=ModerationCategory.PROMPT_INJECTION,
                    pattern=rx.pattern,
                    matched_text=m.group(0),
                    start=m.start(),
                    end=m.end(),
                ))

        return FilterResult(
            is_blocked=bool(hits),
            hits=hits,
            score=min(1.0, len(hits) * 0.25),
        )


_local_filter: Optional[LocalFilter] = None


def get_local_filter() -> LocalFilter:
    """获取全局本地过滤器单例"""
    global _local_filter
    if _local_filter is None:
        _local_filter = LocalFilter()
    return _local_filter
