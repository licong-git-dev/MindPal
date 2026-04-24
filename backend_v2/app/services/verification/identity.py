"""
MindPal Backend V2 - Identity Verifier

实名认证封装。默认未启用（VERIFICATION_ENABLED=false）时所有方法返回 not_configured。

## 可选后端

- aliyun_three_element: 阿里云运营商三要素（姓名 + 身份证 + 手机）
  - 市场价 ¥0.1-0.2 / 次
  - SDK: pip install alibabacloud_dypnsapi20170525
- alipay_realname: 支付宝实名授权
  - 免费（用户授权后回传脱敏数据）
  - 需要集成支付宝 OAuth

## 提供的契约

verify(name, id_card, phone) → VerificationResult

VerificationResult.status ∈ {
  success, mismatch, not_configured, rate_limited, error
}

VerificationResult 不保存 id_card 明文到数据库，只存:
  - is_verified: bool
  - verified_at: datetime
  - id_card_hash: sha256(id_card) 前 16 位（用于"是否同一人"判断，不可反查）
  - birth_year: int  （用于未成年判定，合规"最小必要"）
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class VerificationStatus(str, Enum):
    SUCCESS = "success"              # 认证通过
    MISMATCH = "mismatch"            # 三要素不匹配
    NOT_CONFIGURED = "not_configured"  # 未配置 SDK 或凭证
    RATE_LIMITED = "rate_limited"    # 被三方 API 限流
    INVALID_ID_FORMAT = "invalid_id_format"  # 身份证格式错
    MINOR_DETECTED = "minor_detected"  # 身份证显示未成年
    ERROR = "error"


@dataclass
class VerificationResult:
    status: VerificationStatus
    is_verified: bool = False
    id_card_hash: Optional[str] = None  # sha256 前 16 位，用于"同一人"判断
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    is_minor: bool = False
    error_message: Optional[str] = None


def _extract_birth_from_id_card(id_card: str) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """从二代身份证号（18 位）提取出生年月日。"""
    if len(id_card) != 18:
        return None, None, None
    try:
        return int(id_card[6:10]), int(id_card[10:12]), int(id_card[12:14])
    except ValueError:
        return None, None, None


def _is_valid_id_card_format(id_card: str) -> bool:
    """简单校验二代身份证格式（18 位，最后一位可能是 X）。

    真实校验需计算校验位，这里只做表层校验。
    """
    if not id_card:
        return False
    return bool(re.fullmatch(r"\d{17}[\dXx]", id_card))


def _hash_id_card(id_card: str) -> str:
    """sha256 前 16 位，用于"是否同一人"判断但不可反查。"""
    salt = os.getenv("VERIFICATION_HASH_SALT", "mindpal-id-hash")
    return hashlib.sha256((salt + id_card).encode()).hexdigest()[:16]


def is_verification_enabled() -> bool:
    return os.getenv("VERIFICATION_ENABLED", "false").lower() == "true"


class AliyunThreeElementVerifier:
    """阿里云运营商三要素实现（骨架）。"""

    def __init__(self):
        self.access_key_id = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
        self.access_key_secret = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
        self._sdk_available: Optional[bool] = None

    def _check_sdk(self) -> bool:
        if self._sdk_available is not None:
            return self._sdk_available
        try:
            import alibabacloud_dypnsapi20170525  # noqa: F401
            self._sdk_available = True
        except ImportError:
            self._sdk_available = False
        return self._sdk_available

    @property
    def usable(self) -> bool:
        return (
            bool(self.access_key_id) and bool(self.access_key_secret)
            and is_verification_enabled()
            and self._check_sdk()
        )

    async def verify(
        self,
        name: str,
        id_card: str,
        phone: str,
    ) -> VerificationResult:
        """真实调用阿里云三要素 API。

        当前版本返回 NOT_CONFIGURED，避免因无效凭证产生乱真实调用。
        部署时由运维同学:
          1. pip install alibabacloud_dypnsapi20170525
          2. 填 ALIYUN_ACCESS_KEY_ID / SECRET + VERIFICATION_ENABLED=true
          3. 在此处替换为真实 API 调用
        """
        if not self.usable:
            return VerificationResult(
                status=VerificationStatus.NOT_CONFIGURED,
                error_message="Aliyun three-element SDK or credentials missing"
            )

        # 真实调用的占位（不会执行，因 usable 为 False）
        return VerificationResult(
            status=VerificationStatus.NOT_CONFIGURED,
            error_message="Real API call not wired up yet"
        )


class IdentityVerifier:
    """统一实名认证入口。"""

    def __init__(self):
        self.aliyun = AliyunThreeElementVerifier()

    async def verify(
        self,
        name: str,
        id_card: str,
        phone: str,
    ) -> VerificationResult:
        """执行实名认证。返回标准化结果。"""
        # 1. 格式校验（不花钱）
        if not _is_valid_id_card_format(id_card):
            return VerificationResult(
                status=VerificationStatus.INVALID_ID_FORMAT,
                error_message="Invalid ID card format"
            )

        # 2. 提取出生日期
        by, bm, bd = _extract_birth_from_id_card(id_card)
        is_minor = False
        if by is not None:
            # 当前年份 - 出生年 < 18 认为是未成年
            current_year = datetime.utcnow().year
            is_minor = (current_year - by) < 18

        id_hash = _hash_id_card(id_card)

        # 3. 若身份证显示未成年 → 直接拒绝（不调三方 API 省钱）
        if is_minor:
            return VerificationResult(
                status=VerificationStatus.MINOR_DETECTED,
                is_verified=False,
                id_card_hash=id_hash,
                birth_year=by,
                birth_month=bm,
                birth_day=bd,
                is_minor=True,
                error_message="本服务仅面向 18 周岁及以上成年用户"
            )

        # 4. 调用阿里云三要素
        result = await self.aliyun.verify(name, id_card, phone)
        # 补齐从身份证提取的元数据
        result.id_card_hash = id_hash
        result.birth_year = by
        result.birth_month = bm
        result.birth_day = bd
        result.is_minor = False

        return result


_verifier: Optional[IdentityVerifier] = None


def get_identity_verifier() -> IdentityVerifier:
    global _verifier
    if _verifier is None:
        _verifier = IdentityVerifier()
    return _verifier
