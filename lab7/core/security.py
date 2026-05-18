import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

SECRET_KEY: str = os.getenv(
    "JWT_SECRET_KEY",
    "dev-secret-key-change-me-in-production-please",
)
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class TokenError(Exception):
    """Невалідний або прострочений токен."""


def _build_token(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[dict] = None,
) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    jti = str(uuid.uuid4())

    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": jti,
    }
    if extra_claims:
        payload.update(extra_claims)

    encoded = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded, jti, expires_at


def create_access_token(subject: str, extra_claims: Optional[dict] = None) -> str:
    token, _jti, _exp = _build_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims=extra_claims,
    )
    return token


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Повертає (token, jti, expires_at). jti зберігаємо в БД для ротації."""
    return _build_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: Optional[str] = None) -> dict:
    """
    Декодує JWT і перевіряє підпис та exp.
    Якщо expected_type заданий — також перевіряє поле type у payload.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Токен прострочений") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError(f"Невалідний токен: {exc}") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise TokenError(
            f"Невірний тип токена: очікувався '{expected_type}', "
            f"отримано '{payload.get('type')}'"
        )

    return payload
