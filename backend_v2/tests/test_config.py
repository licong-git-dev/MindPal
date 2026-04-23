import importlib
import sys

import pytest


MODULE_NAME = "app.config"


def load_config_module(monkeypatch, **env):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret")
    monkeypatch.setenv("ALLOWED_ORIGINS", '["http://localhost:3000"]')

    for key, value in env.items():
        monkeypatch.setenv(key, value)

    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


def test_settings_rejects_insecure_secret_when_debug_false(monkeypatch):
    config_module = load_config_module(monkeypatch)

    with pytest.raises(ValueError, match="SECRET_KEY must be explicitly configured"):
        config_module.Settings(
            DEBUG=False,
            SECRET_KEY="local-dev-secret-change-me",
            ALLOWED_ORIGINS=["http://localhost:3000"],
        )


def test_settings_rejects_wildcard_cors_when_debug_false(monkeypatch):
    config_module = load_config_module(monkeypatch)

    with pytest.raises(ValueError, match="Wildcard CORS origin is not allowed"):
        config_module.Settings(
            DEBUG=False,
            SECRET_KEY="a-secure-secret-value",
            ALLOWED_ORIGINS=["http://localhost:3000", "*"],
        )


def test_settings_allows_safe_production_defaults(monkeypatch):
    config_module = load_config_module(monkeypatch)

    settings = config_module.Settings(
        DEBUG=False,
        SECRET_KEY="a-secure-secret-value",
        ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5500"],
    )

    assert settings.DEBUG is False
    assert settings.SECRET_KEY == "a-secure-secret-value"
    assert settings.ALLOWED_ORIGINS == ["http://localhost:3000", "http://localhost:5500"]
