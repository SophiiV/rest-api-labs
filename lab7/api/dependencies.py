from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.rate_limiter import check_rate_limit
from database import get_session
from models.user import User
from repository.book_repository import BookRepository
from repository.user_repository import UserRepository
from services.auth_service import AuthError, AuthService
from services.book_service import BookService


bearer_scheme = HTTPBearer(auto_error=False)


def get_book_service(session: AsyncSession = Depends(get_session)) -> BookService:
    """Створити BookService для поточного запиту (зі своєю сесією БД)."""
    return BookService(BookRepository(session))


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """Створити AuthService для поточного запиту."""
    return AuthService(UserRepository(session))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не передано access-токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await auth_service.get_user_from_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User | None:
    """Повернути User, якщо запит авторизований, або None для анонімів."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        return await auth_service.get_user_from_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_redis(request: Request) -> Redis:
    """Витягти Redis-клієнт з app.state."""
    return request.app.state.redis


async def rate_limit(
    request: Request,
    user: User | None = Depends(get_current_user_optional),
    redis: Redis = Depends(get_redis),
) -> None:
    user_id = user.id if user is not None else None
    client_ip = request.client.host if request.client is not None else "unknown"

    result = await check_rate_limit(redis, user_id=user_id, client_ip=client_ip)
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Перевищено ліміт запитів ({result.limit}/хв). "
                "Спробуйте знову через хвилину."
            ),
            headers={"Retry-After": "60"},
        )
