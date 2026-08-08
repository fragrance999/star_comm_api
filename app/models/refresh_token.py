from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="刷新令牌ID")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属用户ID",
    )
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False, comment="刷新令牌哈希")
    user_agent: Mapped[str | None] = mapped_column(Text, comment="客户端User-Agent")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="过期时间")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="撤销时间")

    user = relationship("User", back_populates="refresh_tokens")
