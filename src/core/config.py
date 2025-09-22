from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field
from typing import List
import os


class Settings(BaseSettings):
	app_name: str = Field(default="AAI Backend", alias="APP_NAME")
	environment: str = Field(default="development", alias="ENVIRONMENT")
	log_level: str = Field(default="info", alias="LOG_LEVEL")

	database_url: str = Field(alias="DATABASE_URL")

	jwt_secret: str = Field(alias="JWT_SECRET")
	algorithm: str = Field(default="HS256", alias="ALGORITHM")
	access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
	refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

	cors_origins: List[AnyHttpUrl] | List[str] = Field(default_factory=list, alias="CORS_ORIGINS")

	class Config:
		case_sensitive = True
		env_file = os.getenv("ENV_FILE", ".env")
		env_file_encoding = "utf-8"


settings = Settings()
