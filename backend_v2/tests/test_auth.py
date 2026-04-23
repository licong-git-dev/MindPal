import asyncio

import pytest
from fastapi import HTTPException, Request, Response

from app.api.v1 import auth


def make_request_with_cookies(cookies=None):
    cookie_header = b""
    if cookies:
        cookie_header = b"; ".join(f"{key}={value}".encode() for key, value in cookies.items())

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/refresh",
        "headers": [(b"cookie", cookie_header)] if cookie_header else [],
    }
    return Request(scope)


def test_set_refresh_cookie_uses_http_only_cookie(monkeypatch):
    monkeypatch.setattr(auth.settings, "DEBUG", False)
    monkeypatch.setattr(auth.settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)
    response = Response()

    auth.set_refresh_cookie(response, "refresh-token-value")

    cookie_header = response.headers["set-cookie"]
    assert "mindpal_refresh_token=refresh-token-value" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=lax" in cookie_header
    assert "Secure" in cookie_header
    assert "Max-Age=604800" in cookie_header


def test_login_response_schema_does_not_expose_refresh_token():
    fields = auth.LoginResponse.model_fields
    assert "refresh_token" not in fields


def test_register_response_schema_does_not_expose_refresh_token():
    fields = auth.RegisterResponse.model_fields
    assert "refresh_token" not in fields


def test_refresh_token_rejects_missing_token_before_db_use():
    async def run_test():
        request = make_request_with_cookies()

        with pytest.raises(HTTPException, match="Refresh token is required") as exc:
            await auth.refresh_token(request=request, token_request=None, db=None)

        assert exc.value.status_code == 401

    asyncio.run(run_test())


def test_refresh_token_rejects_invalid_cookie_token(monkeypatch):
    async def run_test():
        request = make_request_with_cookies({"mindpal_refresh_token": "invalid-token"})
        monkeypatch.setattr(auth, "verify_refresh_token", lambda token: None)

        with pytest.raises(HTTPException, match="Invalid refresh token") as exc:
            await auth.refresh_token(request=request, token_request=None, db=None)

        assert exc.value.status_code == 401

    asyncio.run(run_test())
