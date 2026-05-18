from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import RefreshToken, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        return (await self.session.execute(query)).scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        return (await self.session.execute(query)).scalar_one_or_none()

    async def add_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def add_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_refresh_token(self, jti: str) -> Optional[RefreshToken]:
        query = select(RefreshToken).where(RefreshToken.jti == jti)
        return (await self.session.execute(query)).scalar_one_or_none()

    async def revoke_refresh_token(self, jti: str) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.jti == jti)
            .values(revoked=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()
