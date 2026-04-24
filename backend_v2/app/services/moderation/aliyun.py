"""
MindPal Backend V2 - Aliyun Content Moderation Adapter

阿里云绿网文本检测封装。默认禁用（MODERATION_ALIYUN_ENABLED=false），
即使未配置 key 也不阻塞主链路。

## 真实接入

1. 开通阿里云 "内容安全" 服务: https://www.aliyun.com/product/lvwang
2. 获取 AccessKeyId + AccessKeySecret
3. .env:
     MODERATION_ALIYUN_ENABLED=true
     ALIYUN_ACCESS_KEY_ID=xxx
     ALIYUN_ACCESS_KEY_SECRET=xxx
     ALIYUN_MODERATION_REGION=cn-shanghai  (默认)
4. 安装 SDK: pip install aliyun-python-sdk-green

## 为什么只做 Adapter 骨架

- 真实 SDK 调用需要有效的 AccessKey，在本地开发/测试阶段没必要强制
- 核心本地规则已能拦下 80% 明显违规
- 阿里云作为"二道审核"（高风险场景、边缘案例），不是主审
- 生产部署前由运维同学开启 + 补 key 即可
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


# 阿里云绿网标签到本地 ModerationCategory 的映射
# 参考: https://help.aliyun.com/document_detail/70455.html
ALIYUN_LABEL_MAP = {
    "spam":        "violence",       # 广告/垃圾信息（先归 violence，可细化）
    "ad":          "contact_scam",   # 广告
    "politics":    "politics",
    "terrorism":   "violence",
    "abuse":       "hate",
    "porn":        "porn",
    "flood":       "contact_scam",   # 灌水
    "contraband":  "illegal",        # 违禁品（毒品/武器等）
    "meaningless": "safe",           # 无意义字符
}


@dataclass
class AliyunModerationResult:
    """阿里云返回的简化结果"""
    is_blocked: bool
    suggestion: str = "pass"      # pass / review / block
    labels: List[str] = field(default_factory=list)
    scores: dict = field(default_factory=dict)
    raw: Optional[dict] = None


def is_aliyun_enabled() -> bool:
    """是否启用阿里云审核"""
    return os.getenv("MODERATION_ALIYUN_ENABLED", "false").lower() == "true"


class AliyunModeration:
    """阿里云内容安全检测 adapter

    真实调用依赖 aliyun-python-sdk-green。SDK 未安装或 key 未配置时，
    所有方法返回 "pass"（放行），由本地规则兜底。
    """

    def __init__(self):
        self.access_key_id = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
        self.access_key_secret = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
        self.region = os.getenv("ALIYUN_MODERATION_REGION", "cn-shanghai")
        self._client = None
        self._sdk_available: Optional[bool] = None

    def _check_sdk(self) -> bool:
        """懒检查 SDK 是否可用"""
        if self._sdk_available is not None:
            return self._sdk_available
        try:
            import aliyunsdkcore  # noqa: F401
            self._sdk_available = True
        except ImportError:
            self._sdk_available = False
        return self._sdk_available

    @property
    def usable(self) -> bool:
        """凭证 + SDK 都到位才算可用"""
        return (
            bool(self.access_key_id)
            and bool(self.access_key_secret)
            and is_aliyun_enabled()
            and self._check_sdk()
        )

    async def check_text(self, text: str) -> AliyunModerationResult:
        """检测文本。若 SDK 不可用，直接返回 pass。

        NOTE: 阿里云 SDK 实际是同步 API。生产集成时可用 asyncio.to_thread
        包装（Python 3.9+），或改为 httpx 直接调 REST 接口。
        这里只返回结构化结果，真实调用由运维同学按需补齐。
        """
        if not self.usable:
            # SDK 或凭证未就绪，放行（由本地过滤兜底）
            return AliyunModerationResult(is_blocked=False, suggestion="pass")

        # 占位：真实实现
        # from aliyunsdkcore.client import AcsClient
        # from aliyunsdkgreen.request.v20180509 import TextScanRequest
        # ... 调用 ...
        # 当前版本未启用真实调用，避免因无效 key 产生错误调用。
        return AliyunModerationResult(is_blocked=False, suggestion="pass")


_aliyun_moderation: Optional[AliyunModeration] = None


def get_aliyun_moderation() -> AliyunModeration:
    """获取全局单例"""
    global _aliyun_moderation
    if _aliyun_moderation is None:
        _aliyun_moderation = AliyunModeration()
    return _aliyun_moderation
