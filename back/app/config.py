import os
from os import environ

from dotenv import load_dotenv
from pydantic.v1 import BaseSettings
load_dotenv()


# ========================================
# 说明: 项目配置文件
# ========================================

class Settings(BaseSettings):
    # 项目配置
    PROJECT_NAME: str = "报告小助手"
    PROJECT_DESCRIPTION: str = "报告小助手"
    VERSION: str = "v1"
    DEBUG: bool = environ.get("DEBUG") == "true"
    TEST: bool = False  # environ.get("ENV") not in ["PROD", "DEV"]
    # 秘钥
    SECRET_KEY:str =environ.get("SECRET_KEY")
    ALGORITHM:str =environ.get("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES:str =environ.get("ACCESS_TOKEN_EXPIRE_MINUTES",30)

    # 数据库配置
    POSTGRES_HOST: str = environ.get("POSTGRES_HOST") or "192.168.223.134"  # postgres
    POSTGRES_PORT: str = environ.get("POSTGRES_PORT") or "5432"
    POSTGRES_USER: str = environ.get("POSTGRES_USER") or "postgres"
    POSTGRES_PWD: str = environ.get("POSTGRES_PASSWORD") or "difyai123456"
    POSTGRES_DB: str = environ.get("POSTGRES_DB") or "report"
    DB_POOL_MAX: int = environ.get("DB_POOL_MAX") or 20
    DB_POOL_CONN_LIFE: int = environ.get("DB_POOL_CONN_LIFE") or 600
    TIMEZONE: str = environ.get("TIMEZONE") or "Asia/Shanghai"
    AES_KEY:str=environ.get("AES_KEY") or ""
    MODEL_NAME:str=environ.get("MODEL_NAME") or ""

    # Redis 配置
    REDIS_HOST: str = environ.get("REDIS_HOST") or "192.168.223.134"  # redis
    REDIS_PORT: str = environ.get("REDIS_PORT") or "6379"
    REDIS_USER: str = environ.get("REDIS_USER") or ""
    REDIS_PWD: str = environ.get("REDIS_PWD") or "difyai123456"
    # 邮箱
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    API_URL = os.getenv('API_URL', "https://api.deepseek.com")
    API_KEY = os.getenv('API_KEY', "sk-f8feaed213c942388b68be7e034ad0f9")
    pandoc_path = os.getenv('PANDOC_PATH', "C:\Program Files\Pandoc\pandoc.exe")
    # # 0 库用于后端，1 库用于celery broker
    BASE_REDIS: str = f"redis://{REDIS_USER}:{REDIS_PWD}@{REDIS_HOST}:{REDIS_PORT}/"

    BASE_POSTGRES = f'postgres://{POSTGRES_USER}:{POSTGRES_PWD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    TORTOISE_ORM = {
        "connections": {
            "default": {
                "engine": "tortoise.backends.asyncpg",
                "credentials": {
                    "database": POSTGRES_DB,
                    "host": POSTGRES_HOST,
                    "password": POSTGRES_PWD,
                    "port": POSTGRES_PORT,
                    "user": POSTGRES_USER,
                    "maxsize": DB_POOL_MAX,  # 最大连接数
                    # "minsize": 1, # 最小连接数
                    # 关闭池中非活动连接的秒数。通过 0 则禁用此机制。
                    # "max_inactive_connection_lifetime": 60 * 5,
                    "ssl": False
                },
            }
        },
        "apps": {
            "models": {
                "models": ["aerich.models",
                           "app.models"],
                "default_connection": "default",
            }
        },
        "use_tz": False,
        "timezone": TIMEZONE
    }

    class Config:
        # 启用字段名称大小写敏感性 默认是 False
        case_sensitive = True


settings = Settings()
TORTOISE_ORM = settings.TORTOISE_ORM

