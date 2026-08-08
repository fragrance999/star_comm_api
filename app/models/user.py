from datetime import date

from sqlalchemy import Boolean, Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="用户ID")
    account: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False, comment="登录账号")
    password_hash: Mapped[str] = mapped_column(Text, nullable=False, comment="密码哈希")
    nickname: Mapped[str] = mapped_column(String(20), nullable=False, comment="用户昵称")
    birth_year: Mapped[int] = mapped_column(Integer, nullable=False, comment="出生年份")
    avatar_url: Mapped[str | None] = mapped_column(Text, comment="头像地址")
    invite_code: Mapped[str | None] = mapped_column(String(64), index=True, comment="邀请码")
    accepted_terms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否同意条款")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, comment="账号状态")
    last_login_at: Mapped[date | None] = mapped_column(Date, comment="最后登录日期")

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
