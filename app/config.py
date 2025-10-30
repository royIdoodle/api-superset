from typing import List, Optional
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """项目配置，支持从环境变量与.env文件加载。"""

    # MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "image_oss_manager"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"

    # OSS（阿里云）
    OSS_ENDPOINT: str = "https://oss-your-endpoint.aliyuncs.com"
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    DEFAULT_OSS_BUCKET: str = "common"
    # 可选：支持多个可用桶名
    OSS_BUCKETS: Optional[List[str]] = None

    # TinyPNG
    TINIFY_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_uri(self) -> str:
        password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/"
            f"{self.MYSQL_DB}?charset=utf8mb4"
        )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


