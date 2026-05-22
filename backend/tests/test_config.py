import pytest

from app.config import (
    KNOWN_DEFAULT_ADMIN_PASSWORD,
    KNOWN_DEFAULT_SECRET_KEYS,
    MIN_SECRET_KEY_LENGTH,
    settings,
    validate_production_secrets,
)

# A strong, non-default secret used for the "production passes" scenarios.
STRONG_SECRET = "a" * MIN_SECRET_KEY_LENGTH + "-strong-random-secret-value"
STRONG_AUTH_SECRET = "b" * MIN_SECRET_KEY_LENGTH + "-another-strong-secret"
STRONG_ADMIN_PASSWORD = "not-the-default-admin-password-9f3a"


def _set_strong_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set all secrets to strong, non-default values."""
    monkeypatch.setattr(settings, "SECRET_KEY", STRONG_SECRET)
    monkeypatch.setattr(settings.AUTH, "SECRET_KEY", STRONG_AUTH_SECRET)
    monkeypatch.setattr(settings.ADMIN, "PASSWORD", STRONG_ADMIN_PASSWORD)


class TestValidateProductionSecretsDevBypass:
    def test_debug_true_with_all_repo_defaults_does_not_raise(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", True)
        monkeypatch.setattr(
            settings, "SECRET_KEY", "your-secret-key-change-in-production"
        )
        monkeypatch.setattr(
            settings.AUTH, "SECRET_KEY", "your-secret-key-change-in-production"
        )
        monkeypatch.setattr(settings.ADMIN, "PASSWORD", KNOWN_DEFAULT_ADMIN_PASSWORD)

        assert validate_production_secrets() is None

    def test_debug_true_with_empty_admin_password_does_not_raise(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", True)
        monkeypatch.setattr(settings.ADMIN, "PASSWORD", "   ")

        assert validate_production_secrets() is None


class TestValidateProductionSecretsProductionFailures:
    def test_default_root_secret_key_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        _set_strong_secrets(monkeypatch)
        default_key = next(iter(KNOWN_DEFAULT_SECRET_KEYS))
        monkeypatch.setattr(settings, "SECRET_KEY", default_key)

        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets()

        assert "SECRET_KEY" in str(excinfo.value)

    def test_default_auth_secret_key_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        _set_strong_secrets(monkeypatch)
        default_key = next(iter(KNOWN_DEFAULT_SECRET_KEYS))
        monkeypatch.setattr(settings.AUTH, "SECRET_KEY", default_key)

        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets()

        assert "AUTH_SECRET_KEY" in str(excinfo.value)

    def test_short_root_secret_key_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        _set_strong_secrets(monkeypatch)
        short_secret = "x" * (MIN_SECRET_KEY_LENGTH - 1)
        monkeypatch.setattr(settings, "SECRET_KEY", short_secret)

        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets()

        assert "too short" in str(excinfo.value)

    def test_short_auth_secret_key_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        _set_strong_secrets(monkeypatch)
        short_secret = "y" * (MIN_SECRET_KEY_LENGTH - 1)
        monkeypatch.setattr(settings.AUTH, "SECRET_KEY", short_secret)

        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets()

        assert "too short" in str(excinfo.value)

    def test_default_admin_password_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        _set_strong_secrets(monkeypatch)
        monkeypatch.setattr(settings.ADMIN, "PASSWORD", KNOWN_DEFAULT_ADMIN_PASSWORD)

        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets()

        assert "DEFAULT_ADMIN_PASSWORD" in str(excinfo.value)

    def test_empty_admin_password_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        _set_strong_secrets(monkeypatch)
        monkeypatch.setattr(settings.ADMIN, "PASSWORD", "")

        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets()

        assert "DEFAULT_ADMIN_PASSWORD" in str(excinfo.value)

    def test_whitespace_only_admin_password_raises(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        _set_strong_secrets(monkeypatch)
        monkeypatch.setattr(settings.ADMIN, "PASSWORD", "    \t  ")

        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets()

        assert "DEFAULT_ADMIN_PASSWORD" in str(excinfo.value)

    def test_multiple_problems_all_reported(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        default_key = next(iter(KNOWN_DEFAULT_SECRET_KEYS))
        monkeypatch.setattr(settings, "SECRET_KEY", default_key)
        monkeypatch.setattr(settings.AUTH, "SECRET_KEY", "short")
        monkeypatch.setattr(settings.ADMIN, "PASSWORD", KNOWN_DEFAULT_ADMIN_PASSWORD)

        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets()

        message = str(excinfo.value)
        assert "SECRET_KEY" in message
        assert "AUTH_SECRET_KEY" in message
        assert "DEFAULT_ADMIN_PASSWORD" in message


class TestValidateProductionSecretsProductionPasses:
    def test_all_strong_secrets_does_not_raise(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        _set_strong_secrets(monkeypatch)

        assert validate_production_secrets() is None

    def test_secret_exactly_min_length_does_not_raise(self, monkeypatch):
        monkeypatch.setattr(settings, "DEBUG", False)
        monkeypatch.setattr(settings, "SECRET_KEY", "z" * MIN_SECRET_KEY_LENGTH)
        monkeypatch.setattr(settings.AUTH, "SECRET_KEY", "w" * MIN_SECRET_KEY_LENGTH)
        monkeypatch.setattr(settings.ADMIN, "PASSWORD", STRONG_ADMIN_PASSWORD)

        assert validate_production_secrets() is None


class TestValidateProductionSecretsNoSecretLeak:
    def test_error_message_does_not_contain_secret_values(self, monkeypatch):
        # Short (so they trigger failures) but distinctive secret values.
        leak_secret = "LEAKROOT-secret-xyz"
        leak_auth_secret = "LEAKAUTH-secret-xyz"

        monkeypatch.setattr(settings, "DEBUG", False)
        monkeypatch.setattr(settings, "SECRET_KEY", leak_secret)
        monkeypatch.setattr(settings.AUTH, "SECRET_KEY", leak_auth_secret)
        # Default admin password triggers a failure without leaking a value.
        monkeypatch.setattr(settings.ADMIN, "PASSWORD", KNOWN_DEFAULT_ADMIN_PASSWORD)

        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets()

        message = str(excinfo.value)
        # The actual secret values must never appear in the error message.
        assert leak_secret not in message
        assert leak_auth_secret not in message
        assert KNOWN_DEFAULT_ADMIN_PASSWORD not in message
