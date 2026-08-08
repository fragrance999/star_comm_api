"""add spirit onboarding tables

Revision ID: 20260808_0003
Revises: 20260808_0002
Create Date: 2026-08-08 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260808_0003"
down_revision: str | None = "20260808_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_spirits",
        sa.Column("id", sa.Integer(), nullable=False, comment="星灵ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="所属用户ID"),
        sa.Column("name", sa.String(length=32), nullable=False, comment="星灵名称"),
        sa.Column("appearance_type", sa.String(length=32), nullable=False, comment="星灵形态"),
        sa.Column("persona_type", sa.String(length=32), nullable=False, comment="星灵性格"),
        sa.Column("initiative_level", sa.String(length=32), nullable=False, comment="主动联系频率"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="星灵状态"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_ai_spirits_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_spirits")),
        sa.UniqueConstraint("user_id", name=op.f("uq_ai_spirits_user_id")),
    )
    op.create_index(op.f("ix_ai_spirits_user_id"), "ai_spirits", ["user_id"], unique=False)
    op.create_table(
        "ai_spirit_sessions",
        sa.Column("id", sa.Integer(), nullable=False, comment="会话ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="所属用户ID"),
        sa.Column("spirit_id", sa.Integer(), nullable=False, comment="星灵ID"),
        sa.Column("session_type", sa.String(length=32), nullable=False, comment="会话类型"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="会话状态"),
        sa.Column("user_turn_count", sa.Integer(), nullable=False, comment="用户发言轮数"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["spirit_id"], ["ai_spirits.id"], name=op.f("fk_ai_spirit_sessions_spirit_id_ai_spirits"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_ai_spirit_sessions_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_spirit_sessions")),
    )
    op.create_index(op.f("ix_ai_spirit_sessions_spirit_id"), "ai_spirit_sessions", ["spirit_id"], unique=False)
    op.create_index(op.f("ix_ai_spirit_sessions_user_id"), "ai_spirit_sessions", ["user_id"], unique=False)
    op.create_table(
        "ai_spirit_messages",
        sa.Column("id", sa.Integer(), nullable=False, comment="消息ID"),
        sa.Column("session_id", sa.Integer(), nullable=False, comment="会话ID"),
        sa.Column("role", sa.String(length=16), nullable=False, comment="消息角色"),
        sa.Column("content", sa.Text(), nullable=False, comment="消息内容"),
        sa.Column("message_metadata", sa.JSON(), nullable=True, comment="消息元数据"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["session_id"], ["ai_spirit_sessions.id"], name=op.f("fk_ai_spirit_messages_session_id_ai_spirit_sessions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_spirit_messages")),
    )
    op.create_index(op.f("ix_ai_spirit_messages_session_id"), "ai_spirit_messages", ["session_id"], unique=False)
    op.create_table(
        "user_memories",
        sa.Column("id", sa.Integer(), nullable=False, comment="记忆ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="所属用户ID"),
        sa.Column("spirit_id", sa.Integer(), nullable=False, comment="星灵ID"),
        sa.Column("category", sa.String(length=32), nullable=False, comment="记忆分类"),
        sa.Column("content", sa.Text(), nullable=False, comment="记忆内容"),
        sa.Column("source_type", sa.String(length=32), nullable=False, comment="记忆来源"),
        sa.Column("confidence", sa.Float(), nullable=False, comment="置信度"),
        sa.Column("confirmation_status", sa.String(length=32), nullable=False, comment="确认状态"),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, comment="是否敏感"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, comment="是否启用"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["spirit_id"], ["ai_spirits.id"], name=op.f("fk_user_memories_spirit_id_ai_spirits"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_user_memories_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_memories")),
        sa.UniqueConstraint("id", "user_id", name=op.f("uq_user_memories_id_user_id")),
    )
    op.create_index(op.f("ix_user_memories_spirit_id"), "user_memories", ["spirit_id"], unique=False)
    op.create_index(op.f("ix_user_memories_user_id"), "user_memories", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_memories_user_id"), table_name="user_memories")
    op.drop_index(op.f("ix_user_memories_spirit_id"), table_name="user_memories")
    op.drop_table("user_memories")
    op.drop_index(op.f("ix_ai_spirit_messages_session_id"), table_name="ai_spirit_messages")
    op.drop_table("ai_spirit_messages")
    op.drop_index(op.f("ix_ai_spirit_sessions_user_id"), table_name="ai_spirit_sessions")
    op.drop_index(op.f("ix_ai_spirit_sessions_spirit_id"), table_name="ai_spirit_sessions")
    op.drop_table("ai_spirit_sessions")
    op.drop_index(op.f("ix_ai_spirits_user_id"), table_name="ai_spirits")
    op.drop_table("ai_spirits")
