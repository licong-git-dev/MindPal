"""
MindPal Backend V2 - Identity Verification Package

对应 DEEP_AUDIT_V3 P3-1 GAP-4 及
《生成式人工智能服务管理暂行办法》§9（要求真实身份信息）。

当前版本提供骨架和 API 契约，真实调用需:
  1. 开通阿里云运营商三要素认证或支付宝实名认证
  2. 在 .env 配置 VERIFICATION_* 凭证
  3. 安装相应 SDK（见 identity.py 注释）

骨架在凭证缺失时返回 "not_configured"，不会造成生产环境崩溃。
"""

from app.services.verification.identity import (
    IdentityVerifier,
    VerificationResult,
    VerificationStatus,
    get_identity_verifier,
)

__all__ = [
    "IdentityVerifier",
    "VerificationResult",
    "VerificationStatus",
    "get_identity_verifier",
]
