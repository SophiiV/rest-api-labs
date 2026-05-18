from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import RefreshToken, User


class UserRepository:
    """CRUD-операції над таблицями users та refresh_tokens."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    async def get_by_username(self, username: str) -> Optional[User]:
        """Знайти користувача за username (для логіну та перевірки унікальності)."""
        query = select(User).where(User.username == username)
        return (await self.session.execute(query)).scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Знайти користувача за id (для get_current_user)."""
        query = select(User).where(User.id == user_id)
        return (await self.session.execute(query)).scalar_one_or_none()

    async def add_user(self, user: User) -> User:
        """Додати нового користувача."""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    # ------------------------------------------------------------------
    # Refresh tokens
    # ------------------------------------------------------------------
    async def add_refresh_token(self, token: RefreshToken) -> RefreshToken:
        """Зберегти виданий refresh-токен."""
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_refresh_token(self, jti: str) -> Optional[RefreshToken]:
        """Знайти refresh-токен по jti."""
        query = select(RefreshToken).where(RefreshToken.jti == jti)
        return (await self.session.execute(query)).scalar_one_or_none()

    async def revoke_refresh_token(self, jti: str) -> None:
        """
        Позначити refresh-токен як revoked.
        Викликається при /auth/refresh (одноразове використання) і /auth/logout.
        """
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.jti == jti)
            .values(revoked=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """
        Відкликати ВСІ активні refresh-токени користувача.
        Використовується при logout-всюди / зміні пароля / детекції компрометації.
        """
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()
