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
    pass


class CredentialsError(AuthError):
    pass


class UserAlreadyExistsError(AuthError):
    pass


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def register(self, data: UserCreate) -> User:
        existing = await self.repository.get_by_username(data.username)
        if existing is not None:
            raise UserAlreadyExistsError(f"Користувач '{data.username}' вже існує")

        user = User(
            username=data.username,
            hashed_password=hash_password(data.password),
        )
        return await self.repository.add_user(user)

    async def login(self, data: UserLogin) -> Tuple[str, str]:
        user = await self.repository.get_by_username(data.username)
        # однакова помилка для "не знайдено" і "невірний пароль" — щоб не розкривати список юзерів
        if user is None or not verify_password(data.password, user.hashed_password):
            raise CredentialsError("Невірне ім'я користувача або пароль")

        if not user.is_active:
            raise CredentialsError("Користувач деактивований")

        return await self._issue_token_pair(user)

    async def refresh(self, refresh_token_str: str) -> Tuple[str, str]:
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
            # повторне використання revoked-токена — відкликаємо всі сесії
            await self.repository.revoke_all_user_tokens(token_record.user_id)
            raise AuthError(
                "Refresh-токен уже був використаний (можлива компрометація). "
                "Усі сесії відкликано — увійдіть знову."
            )

        if token_record.expires_at < datetime.utcnow():
            raise AuthError("Refresh-токен прострочений (за версією БД)")

        user = await self.repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthError("Користувача не знайдено або він деактивований")

        await self.repository.revoke_refresh_token(jti)
        return await self._issue_token_pair(user)

    async def logout(self, refresh_token_str: str) -> None:
        try:
            payload = decode_token(refresh_token_str, expected_type="refresh")
            jti = payload.get("jti")
            if jti:
                await self.repository.revoke_refresh_token(jti)
        except TokenError:
            return  # logout з битим токеном — ігноруємо

    async def get_user_from_access_token(self, access_token: str) -> User:
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

    async def _issue_token_pair(self, user: User) -> Tuple[str, str]:
        access = create_access_token(subject=user.id, extra_claims={"username": user.username})
        refresh, jti, expires_at = create_refresh_token(subject=user.id)

        await self.repository.add_refresh_token(
            RefreshToken(jti=jti, user_id=user.id, expires_at=expires_at, revoked=False)
        )
        return access, refresh
