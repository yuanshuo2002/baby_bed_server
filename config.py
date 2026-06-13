"""
应用配置管理模块
使用 pydantic-settings 从 .env 文件读取配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ========== 数据库配置 ==========
    DB_HOST: str = "223.247.96.246"
    DB_PORT: int = 3306
    DB_USER: str = "baby_bed_sql"
    DB_PASSWORD: str = "baby_bed_sql"
    DB_NAME: str = "baby_bed_sql"

    @property
    def DATABASE_URL(self) -> str:
        """构建异步数据库连接URL"""
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """构建同步数据库连接URL（用于迁移等工具）"""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # ========== JWT配置 ==========
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24小时

    # ========== Redis配置 ==========
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        """构建Redis连接URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ========== 讯飞API配置 ==========
    XUNFEI_APP_ID: str = ""
    XUNFEI_API_KEY: str = ""
    XUNFEI_API_SECRET: str = ""

    # ========== 微信小程序配置 ==========
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # ========== 外部API地址 ==========
    LLM_API_URL: str = "http://127.0.0.1:8001/v1/chat/completions"
    LLM_API_KEY: str = ""
    TTS_API_URL: str = "http://223.247.96.246:8002/tts"
    ASR_API_URL: str = "http://223.247.96.246:8003/asr"

    # ========== 语音克隆API (http://223.247.96.246:30028/v1/audio/) ==========
    VOICE_CLONE_API_URL: str = "http://223.247.96.246:30028/v1/audio"
    VOICE_CLONE_API_KEY: str = ""

    # ========== 长记忆(LTM)管理服务 ==========
    LTM_API_URL: str = "http://223.247.96.246:8122"

    # ========== 应用配置 ==========
    APP_NAME: str = "Baby Bed Server"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"


# 全局配置实例
settings = Settings()
