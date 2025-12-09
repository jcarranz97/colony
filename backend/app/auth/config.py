from pydantic_settings import BaseSettings  # Changed import
from typing import Optional


class AuthSettings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OAuth2 Settings
    TOKEN_URL: str = "auth/login"

    class Config:
        env_file = ".env"
        env_prefix = "AUTH_"


auth_settings = AuthSettings()
