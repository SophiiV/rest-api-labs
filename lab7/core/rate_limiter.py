"""
Rate Limiter — метод фіксованого вікна (Fixed Window).

Авторизовані: 10 запитів/хв (по user_id)
Анонімні:      2 запити/хв  (по IP)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from redis.asyncio import Redis

AUTHENTICATED_LIMIT: int = 10
ANONYMOUS_LIMIT: int = 2
WINDOW_SECONDS: int = 60


@dataclass
class RateLimitResult:
    allowed: bool
    current: int
    limit: int
    scope: str  # "user" або "anon"


async def check_rate_limit(
    redis: Redis,
    *,
    user_id: Optional[str],
    client_ip: str,
) -> RateLimitResult:
    if user_id is not None:
        scope = "user"
        ident = user_id
        limit = AUTHENTICATED_LIMIT
    else:
        scope = "anon"
        ident = client_ip
        limit = ANONYMOUS_LIMIT

    key = f"rate_limit:{scope}:{ident}"

    # INCR атомарно інкрементує лічильник; повертає нове значення
    current = await redis.incr(key)

    # якщо ключ щойно створено — ставимо TTL 60 с
    if current == 1:
        await redis.expire(key, WINDOW_SECONDS)

    allowed = current <= limit
    return RateLimitResult(allowed=allowed, current=current, limit=limit, scope=scope)
