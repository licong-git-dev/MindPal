"""
MindPal Backend V2 - FastAPI Configuration
"""

from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    APP_NAME: str = "MindPal API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置 (支持SQLite用于本地开发)
    DATABASE_URL: str = "sqlite+aiosqlite:///./mindpal_v2.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant配置
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # JWT配置
    SECRET_KEY: str = "local-dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS配置
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5500", "http://127.0.0.1:5500"]

    # LLM配置
    # 阿里云通义千问
    DASHSCOPE_API_KEY: Optional[str] = None
    QWEN_MODEL: str = "qwen-max"

    # Anthropic Claude
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-sonnet-20240229"

    # 火山引擎(备用)
    VOLC_ACCESS_KEY: Optional[str] = None
    VOLC_SECRET_KEY: Optional[str] = None

    # 阿里云语音服务
    ALIYUN_TTS_APP_KEY: Optional[str] = None
    ALIYUN_ASR_APP_KEY: Optional[str] = None
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None

    # 微信支付
    WECHAT_APP_ID: Optional[str] = None
    WECHAT_MCH_ID: Optional[str] = None
    WECHAT_API_KEY: Optional[str] = None
    WECHAT_API_V3_KEY: Optional[str] = None
    WECHAT_SERIAL_NO: Optional[str] = None
    WECHAT_PRIVATE_KEY: Optional[str] = None
    WECHAT_NOTIFY_URL: Optional[str] = None

    # 支付宝
    ALIPAY_APP_ID: Optional[str] = None
    ALIPAY_PRIVATE_KEY: Optional[str] = None
    ALIPAY_PUBLIC_KEY: Optional[str] = None
    ALIPAY_ALIPAY_PUBLIC_KEY: Optional[str] = None
    ALIPAY_NOTIFY_URL: Optional[str] = None
    ALIPAY_RETURN_URL: Optional[str] = None
    ALIPAY_SANDBOX: bool = True

    # 游戏配置
    DEFAULT_GOLD: int = 1000
    DEFAULT_DIAMONDS: int = 0
    MAX_INVENTORY_SLOTS: int = 48

    # 配额配置
    FREE_DAILY_CHAT_LIMIT: int = 100
    FREE_DAILY_VOICE_LIMIT: int = 10
    PREMIUM_DAILY_CHAT_LIMIT: int = -1  # 无限
    PREMIUM_DAILY_VOICE_LIMIT: int = -1

    @model_validator(mode="after")
    def validate_security_defaults(self):
        insecure_secret = self.SECRET_KEY in {"", "local-dev-secret-change-me", "your-super-secret-key-change-in-production"}
        has_wildcard_origin = "*" in self.ALLOWED_ORIGINS

        if not self.DEBUG and insecure_secret:
            raise ValueError("SECRET_KEY must be explicitly configured when DEBUG is false")

        if not self.DEBUG and has_wildcard_origin:
            raise ValueError("Wildcard CORS origin is not allowed when DEBUG is false")

        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
