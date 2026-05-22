from pydantic_settings import BaseSettings  # Changed import

# Known repo-default secret placeholders. These ship in the repo on purpose
# for local/dev convenience (docker-compose, pytest) but MUST never be used
# in production. The values are intentionally kept in this file and in
# helm/colony/values.yaml; production startup is blocked instead of removing
# them. Keep this set in sync with:
#   - AuthSettings.SECRET_KEY / Settings.SECRET_KEY defaults below
#   - helm/colony/values.yaml backend.env.secretKey default
KNOWN_DEFAULT_SECRET_KEYS: frozenset[str] = frozenset(
    {
        "your-secret-key-change-in-production",
        "change-me-in-production-generate-a-strong-random-secret",
    }
)

# Known repo-default admin password. Kept in this file and in
# helm/colony/values.yaml (defaultAdminPassword); production startup is
# blocked if it is still in use.
KNOWN_DEFAULT_ADMIN_PASSWORD: str = "colony-admin"

# Minimum acceptable length for a JWT signing secret in production.
MIN_SECRET_KEY_LENGTH: int = 32


class AuthSettings(BaseSettings):
    """Authentication related settings."""

    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OAuth2 Settings
    TOKEN_URL: str = "auth/login"

    class Config:
        """Configuration for environment variable prefix."""

        env_prefix = "AUTH_"


class AdminSettings(BaseSettings):
    """Default admin user settings — used by the seeder on first deploy."""

    USERNAME: str = "admin"
    PASSWORD: str = "colony-admin"

    class Config:
        """Configuration for environment variable prefix."""

        env_prefix = "DEFAULT_ADMIN_"


class Settings(BaseSettings):
    """Application configuration settings."""

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

    # Admin settings
    ADMIN: AdminSettings = AdminSettings()

    class Config:
        """Configuration for environment file."""

        env_file = ".env"


settings = Settings()


def validate_production_secrets() -> None:
    """Refuse to start in production when repo-default secrets are still set.

    Fails closed: when ``settings.DEBUG`` is ``False`` (production — the Helm
    chart sets ``DEBUG=false``), this raises a fatal :class:`RuntimeError`
    that aborts startup if any of the following holds:

    * ``settings.SECRET_KEY`` or ``settings.AUTH.SECRET_KEY`` equals one of
      :data:`KNOWN_DEFAULT_SECRET_KEYS`, or is shorter than
      :data:`MIN_SECRET_KEY_LENGTH` characters.
    * ``settings.ADMIN.PASSWORD`` equals
      :data:`KNOWN_DEFAULT_ADMIN_PASSWORD`, or is empty / whitespace-only.

    When ``settings.DEBUG`` is ``True`` (local dev, docker-compose, pytest)
    the defaults are permitted and this function returns without raising.
    Secret values are never included in the error message.

    Raises:
        RuntimeError: If running in production with an insecure secret.
    """
    if settings.DEBUG:
        return

    problems: list[str] = []

    secret_targets = (
        ("SECRET_KEY", settings.SECRET_KEY),
        ("AUTH_SECRET_KEY", settings.AUTH.SECRET_KEY),
    )
    for name, value in secret_targets:
        if value in KNOWN_DEFAULT_SECRET_KEYS:
            problems.append(
                f"{name} is still set to a known repo-default placeholder. "
                f"Set a strong random {name} (>={MIN_SECRET_KEY_LENGTH} "
                "chars), e.g. via helm/colony/values.yaml "
                "backend.env.secretKey "
                '(generate: python -c "import secrets; '
                'print(secrets.token_hex(32))").'
            )
        elif len(value) < MIN_SECRET_KEY_LENGTH:
            problems.append(
                f"{name} is too short (must be >="
                f"{MIN_SECRET_KEY_LENGTH} chars). Set a strong random "
                f"{name} via helm/colony/values.yaml backend.env.secretKey."
            )

    admin_password = settings.ADMIN.PASSWORD
    if admin_password == KNOWN_DEFAULT_ADMIN_PASSWORD:
        problems.append(
            "DEFAULT_ADMIN_PASSWORD is still set to the known repo-default. "
            "Set a strong DEFAULT_ADMIN_PASSWORD via helm/colony/values.yaml "
            "backend.env.defaultAdminPassword before deploying."
        )
    elif not admin_password.strip():
        problems.append(
            "DEFAULT_ADMIN_PASSWORD is empty or whitespace-only. Set a "
            "strong DEFAULT_ADMIN_PASSWORD via helm/colony/values.yaml "
            "backend.env.defaultAdminPassword."
        )

    if problems:
        joined = "\n  - ".join(problems)
        raise RuntimeError(
            "Refusing to start: insecure default secret(s) detected in "
            "production (DEBUG=false):\n  - "
            f"{joined}"
        )
