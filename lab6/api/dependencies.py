from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models.user import User
from repository.book_repository import BookRepository
from repository.user_repository import UserRepository
from services.auth_service import AuthError, AuthService
from services.book_service import BookService


# ----------------------------------------------------------------------
# HTTPBearer — найпростіша схема FastAPI для Bearer-токенів.
# ----------------------------------------------------------------------
bearer_scheme = HTTPBearer(auto_error=False)


# ----------------------------------------------------------------------
# Service factories
# ----------------------------------------------------------------------
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
    """
    Витягнути access-токен із заголовка Authorization: Bearer <token>,
    декодувати його та повернути об'єкт користувача.

    Будь-яка проблема (нема заголовка, токен битий, прострочений, не той тип)
    → 401 Unauthorized з заголовком WWW-Authenticate: Bearer
    """
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
