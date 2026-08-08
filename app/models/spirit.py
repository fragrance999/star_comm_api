from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AiSpirit(TimestampMixin, Base):
    __tablename__ = "ai_spirits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="星灵ID")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False, comment="所属用户ID"
    )
    name: Mapped[str] = mapped_column(String(32), default="星灵", nullable=False, comment="星灵名称")
    appearance_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="星灵形态")
    persona_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="星灵性格")
    initiative_level: Mapped[str] = mapped_column(String(32), nullable=False, comment="主动联系频率")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, comment="星灵状态")

    user = relationship("User", back_populates="spirit")
    sessions = relationship("AiSpiritSession", back_populates="spirit", cascade="all, delete-orphan")


class AiSpiritSession(TimestampMixin, Base):
    __tablename__ = "ai_spirit_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="会话ID")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False, comment="所属用户ID"
    )
    spirit_id: Mapped[int] = mapped_column(
        ForeignKey("ai_spirits.id", ondelete="CASCADE"), index=True, nullable=False, comment="星灵ID"
    )
    session_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="会话类型")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, comment="会话状态")
    user_turn_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="用户发言轮数")

    spirit = relationship("AiSpirit", back_populates="sessions")
    messages = relationship("AiSpiritMessage", back_populates="session", cascade="all, delete-orphan")


class AiSpiritMessage(TimestampMixin, Base):
    __tablename__ = "ai_spirit_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="消息ID")
    session_id: Mapped[int] = mapped_column(
        ForeignKey("ai_spirit_sessions.id", ondelete="CASCADE"), index=True, nullable=False, comment="会话ID"
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False, comment="消息角色")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    message_metadata: Mapped[dict[str, object] | None] = mapped_column(JSON, comment="消息元数据")

    session = relationship("AiSpiritSession", back_populates="messages")


class UserMemory(TimestampMixin, Base):
    __tablename__ = "user_memories"
    __table_args__ = (UniqueConstraint("id", "user_id", name="uq_user_memories_id_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="记忆ID")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False, comment="所属用户ID"
    )
    spirit_id: Mapped[int] = mapped_column(
        ForeignKey("ai_spirits.id", ondelete="CASCADE"), index=True, nullable=False, comment="星灵ID"
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False, comment="记忆分类")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="记忆内容")
    source_type: Mapped[str] = mapped_column(String(32), default="ONBOARDING", nullable=False, comment="记忆来源")
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False, comment="置信度")
    confirmation_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, comment="确认状态")
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否敏感")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否启用")
