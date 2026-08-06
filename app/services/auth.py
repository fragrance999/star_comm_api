from datetime import UTC, datetime, timedelta
from hashlib import sha256

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, payload: RegisterRequest) -> User:
        if settings.register_mode == "CLOSED":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is closed")
        if settings.register_mode == "INVITE_REQUIRED" and not payload.invite_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite code is required")
        if not payload.accepted_terms:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Terms must be accepted")

        existing = await self.db.execute(select(User).where(User.account == payload.account))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")

        user = User(
            account=payload.account,
            password_hash=hash_password(payload.password),
            nickname=payload.nickname,
            birth_year=payload.birth_year,
            avatar_url=payload.avatar_url,
            invite_code=payload.invite_code,
            accepted_terms=payload.accepted_terms,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, payload: LoginRequest) -> TokenPair:
        result = await self.db.execute(select(User).where(User.account == payload.account))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect account or password")
        if user.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
        return await self._issue_token_pair(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token, expected_type="refresh")
        token_hash = self._hash_token(refresh_token)
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.revoked_at.is_(None))
        )
        stored_token = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if stored_token is None or stored_token.expires_at <= now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        try:
            user_id = int(payload["sub"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or user.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        stored_token.revoked_at = now
        return await self._issue_token_pair(user)

    async def logout(self, refresh_token: str) -> None:
        token_hash = self._hash_token(refresh_token)
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.revoked_at.is_(None))
        )
        stored_token = result.scalar_one_or_none()
        if stored_token is not None:
            stored_token.revoked_at = datetime.now(UTC)
            await self.db.commit()

    async def _issue_token_pair(self, user: User) -> TokenPair:
        access_token = create_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
            token_type="access",
        )
        refresh_token = create_token(
            subject=str(user.id),
            expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
            token_type="refresh",
        )
        stored_token = RefreshToken(
            user_id=user.id,
            token_hash=self._hash_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
        self.db.add(stored_token)
        await self.db.commit()
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def _hash_token(token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()
