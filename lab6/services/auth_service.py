from datetime import datetime
from typing import Tuple

from core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.user import RefreshToken, User
from repository.user_repository import UserRepository
from schemas.auth import UserCreate, UserLogin


class AuthError(Exception):
    """Базова помилка авторизації (логін/реєстрація/токен)."""


class CredentialsError(AuthError):
    """Невірне ім'я користувача або пароль."""


class UserAlreadyExistsError(AuthError):
    """Username вже зайнятий."""


class AuthService:
    """Бізнес-логіка автентифікації."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    # ------------------------------------------------------------------
    # Реєстрація
    # ------------------------------------------------------------------
    async def register(self, data: UserCreate) -> User:
        existing = await self.repository.get_by_username(data.username)
        if existing is not None:
            raise UserAlreadyExistsError(
                f"Користувач '{data.username}' вже існує"
            )

        user = User(
            username=data.username,
            hashed_password=hash_password(data.password),
        )
        return await self.repository.add_user(user)

    # ------------------------------------------------------------------
    # Логін — видача пари токенів
    # ------------------------------------------------------------------
    async def login(self, data: UserLogin) -> Tuple[str, str]:
        """
        Перевірити креденшіали і видати (access_token, refresh_token).
        """
        user = await self.repository.get_by_username(data.username)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise CredentialsError("Невірне ім'я користувача або пароль")

        if not user.is_active:
            raise CredentialsError("Користувач деактивований")

        return await self._issue_token_pair(user)

    # ------------------------------------------------------------------
    # Refresh — ротація токенів
    # ------------------------------------------------------------------
    async def refresh(self, refresh_token_str: str) -> Tuple[str, str]:
        """
        Refresh token rotation:
          1) Декодуємо refresh-токен (перевірка підпису + exp + type)
          2) Знаходимо запис у БД по jti
          3) Перевіряємо, що він НЕ revoked
          4) Позначаємо старий токен як revoked
          5) Видаємо НОВУ пару токенів
        """
        try:
            payload = decode_token(refresh_token_str, expected_type="refresh")
        except TokenError as exc:
            raise AuthError(f"Refresh-токен невалідний: {exc}") from exc

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise AuthError("Refresh-токен пошкоджений (немає jti/sub)")

        token_record = await self.repository.get_refresh_token(jti)
        if token_record is None:
            raise AuthError("Refresh-токен не зареєстрований у системі")

        if token_record.revoked:
            await self.repository.revoke_all_user_tokens(token_record.user_id)
            raise AuthError(
                "Refresh-токен уже був використаний (можлива компрометація). "
                "Усі сесії відкликано — увійдіть знову."
            )

        if token_record.expires_at < datetime.utcnow():
            raise AuthError("Refresh-токен прострочений (за версією БД)")

        # Знаходимо користувача
        user = await self.repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthError("Користувача не знайдено або він деактивований")

        # Ротація: revoke старого і видача нової пари
        await self.repository.revoke_refresh_token(jti)
        return await self._issue_token_pair(user)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------
    async def logout(self, refresh_token_str: str) -> None:
        """
        Відкликати конкретний refresh-токен (вийти з цього пристрою).
        Якщо токен битий — мовчки ігноруємо (logout має бути ідемпотентним).
        """
        try:
            payload = decode_token(refresh_token_str, expected_type="refresh")
            jti = payload.get("jti")
            if jti:
                await self.repository.revoke_refresh_token(jti)
        except TokenError:
            # Logout з битим токеном — теж OK
            return

    # ------------------------------------------------------------------
    # Перевірка access-токена → User (для get_current_user dependency)
    # ------------------------------------------------------------------
    async def get_user_from_access_token(self, access_token: str) -> User:
        """
        Розкодувати access-токен і повернути User, або кинути AuthError.
        Викликається з кожного захищеного запиту до /books.
        """
        try:
            payload = decode_token(access_token, expected_type="access")
        except TokenError as exc:
            raise AuthError(str(exc)) from exc

        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Access-токен пошкоджений")

        user = await self.repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthError("Користувача не знайдено або він деактивований")
        return user

    # ------------------------------------------------------------------
    # видача пари (access + refresh) із збереженням refresh у БД
    # ------------------------------------------------------------------
    async def _issue_token_pair(self, user: User) -> Tuple[str, str]:
        access = create_access_token(subject=user.id, extra_claims={"username": user.username})
        refresh, jti, expires_at = create_refresh_token(subject=user.id)

        await self.repository.add_refresh_token(
            RefreshToken(jti=jti, user_id=user.id, expires_at=expires_at, revoked=False)
        )
        return access, refresh
