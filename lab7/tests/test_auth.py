import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"


# --- Реєстрація ---

@pytest.mark.asyncio
async def test_register_creates_user(client: AsyncClient):
    r = await client.post(REGISTER_URL, json={"username": "alice", "password": "secret123"})
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "alice"
    assert body["is_active"] is True
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_username_returns_409(client: AsyncClient):
    await client.post(REGISTER_URL, json={"username": "bob", "password": "secret123"})
    r = await client.post(REGISTER_URL, json={"username": "bob", "password": "another1"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password_returns_422(client: AsyncClient):
    r = await client.post(REGISTER_URL, json={"username": "carol", "password": "x"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_short_username_returns_422(client: AsyncClient):
    r = await client.post(REGISTER_URL, json={"username": "ab", "password": "secret123"})
    assert r.status_code == 422


# --- Логін ---

@pytest.mark.asyncio
async def test_login_returns_token_pair(client: AsyncClient):
    await client.post(REGISTER_URL, json={"username": "dave", "password": "secret123"})
    r = await client.post(LOGIN_URL, json={"username": "dave", "password": "secret123"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and len(body["access_token"]) > 20
    assert "refresh_token" in body and len(body["refresh_token"]) > 20
    assert body["token_type"] == "bearer"
    assert body["access_token"] != body["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post(REGISTER_URL, json={"username": "eve", "password": "secret123"})
    r = await client.post(LOGIN_URL, json={"username": "eve", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user_returns_401(client: AsyncClient):
    r = await client.post(LOGIN_URL, json={"username": "ghost", "password": "any12345"})
    assert r.status_code == 401


# --- /auth/me ---

@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient, auth_headers: dict):
    r = await client.get(ME_URL, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient):
    r = await client.get(ME_URL)
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_with_garbage_token_returns_401(client: AsyncClient):
    r = await client.get(ME_URL, headers={"Authorization": "Bearer not.a.real.jwt"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_with_refresh_token_in_bearer_returns_401(
    client: AsyncClient, auth_tokens: dict
):
    """Refresh-токен не повинен працювати замість access-токена."""
    headers = {"Authorization": f"Bearer {auth_tokens['refresh_token']}"}
    r = await client.get(ME_URL, headers=headers)
    assert r.status_code == 401


# --- Refresh і ротація ---

@pytest.mark.asyncio
async def test_refresh_returns_new_token_pair(client: AsyncClient, auth_tokens: dict):
    r = await client.post(REFRESH_URL, json={"refresh_token": auth_tokens["refresh_token"]})
    assert r.status_code == 200
    body = r.json()
    assert body["refresh_token"] != auth_tokens["refresh_token"]
    assert body["access_token"] != auth_tokens["access_token"]


@pytest.mark.asyncio
async def test_refresh_old_token_after_rotation_returns_401(
    client: AsyncClient, auth_tokens: dict
):
    """Refresh token rotation: повторне використання старого refresh-токена → 401."""
    old_refresh = auth_tokens["refresh_token"]

    r1 = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    assert r1.status_code == 200

    r2 = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_garbage_returns_401(client: AsyncClient):
    r = await client.post(REFRESH_URL, json={"refresh_token": "not-a-real-token"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_access_token_returns_401(
    client: AsyncClient, auth_tokens: dict
):
    """Access-токен не повинен спрацювати на /refresh."""
    r = await client.post(REFRESH_URL, json={"refresh_token": auth_tokens["access_token"]})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_new_access_token_after_refresh_works(client: AsyncClient, auth_tokens: dict):
    r = await client.post(REFRESH_URL, json={"refresh_token": auth_tokens["refresh_token"]})
    new_access = r.json()["access_token"]

    r2 = await client.get(ME_URL, headers={"Authorization": f"Bearer {new_access}"})
    assert r2.status_code == 200
    assert r2.json()["username"] == "testuser"


# --- Logout ---

@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient, auth_tokens: dict):
    refresh = auth_tokens["refresh_token"]
    r = await client.post(LOGOUT_URL, json={"refresh_token": refresh})
    assert r.status_code == 204

    r2 = await client.post(REFRESH_URL, json={"refresh_token": refresh})
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_logout_with_invalid_token_is_idempotent(client: AsyncClient):
    """Logout з битим токеном повертає 204."""
    r = await client.post(LOGOUT_URL, json={"refresh_token": "garbage-token"})
    assert r.status_code == 204
