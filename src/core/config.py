from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field
from typing import List
import os


class Settings(BaseSettings):
    APP_NAME: str = Field(default="AAI Backend", alias="APP_NAME")
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")
    DATABASE_URL: str = Field(alias="DATABASE_URL")

    JWT_SECRET: str = Field(alias="JWT_SECRET")
    ALGORITHM: str = Field(default="HS256", alias="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    CORS_ORIGINS: List[AnyHttpUrl] | List[str] = Field(
        default_factory=list, alias="CORS_ORIGINS"
    )

    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", alias="LOG_FORMAT")

    class Config:
        case_sensitive = True
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"

    # Convenience accessors (snake_case) for callers using lowercase names
    @property
    def jwt_secret(self) -> str:
        return self.JWT_SECRET

    @property
    def algorithm(self) -> str:
        return self.ALGORITHM

    @property
    def access_token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_expire_days(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS


settings = Settings()
