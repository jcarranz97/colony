from pydantic_settings import BaseSettings  # Changed import


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

    class Config:
        env_file = ".env"


settings = Settings()
