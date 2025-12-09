from pydantic_settings import BaseSettings  # Changed import


class AuthSettings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OAuth2 Settings
    TOKEN_URL: str = "auth/login"

    class Config:
        env_prefix = "AUTH_"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Colony API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = (
        "postgresql://colony_user:colony_password@localhost:5432/colony_db"
    )

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # CORS
    ALLOWED_HOSTS: list = ["http://localhost:3000"]

    # Auth settings
    AUTH: AuthSettings = AuthSettings()

    class Config:
        env_file = ".env"


settings = Settings()
