from datetime import date

from sqlalchemy import Boolean, Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    nickname: Mapped[str] = mapped_column(String(20), nullable=False)
    birth_year: Mapped[int] = mapped_column(Integer, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    invite_code: Mapped[str | None] = mapped_column(String(64), index=True)
    accepted_terms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    last_login_at: Mapped[date | None] = mapped_column(Date)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
