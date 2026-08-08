"""initial auth tables

Revision ID: 20260806_0001
Revises:
Create Date: 2026-08-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260806_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column("account", sa.String(length=255), nullable=False, comment="登录账号"),
        sa.Column("password_hash", sa.Text(), nullable=False, comment="密码哈希"),
        sa.Column("nickname", sa.String(length=20), nullable=False, comment="用户昵称"),
        sa.Column("birth_year", sa.Integer(), nullable=False, comment="出生年份"),
        sa.Column("avatar_url", sa.Text(), nullable=True, comment="头像地址"),
        sa.Column("invite_code", sa.String(length=64), nullable=True, comment="邀请码"),
        sa.Column("accepted_terms", sa.Boolean(), nullable=False, comment="是否同意条款"),
        sa.Column("status", sa.String(length=32), nullable=False, comment="账号状态"),
        sa.Column("last_login_at", sa.Date(), nullable=True, comment="最后登录日期"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("account", name=op.f("uq_users_account")),
    )
    op.create_index(op.f("ix_users_account"), "users", ["account"], unique=False)
    op.create_index(op.f("ix_users_invite_code"), "users", ["invite_code"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False, comment="刷新令牌ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="所属用户ID"),
        sa.Column("token_hash", sa.String(length=128), nullable=False, comment="刷新令牌哈希"),
        sa.Column("user_agent", sa.Text(), nullable=True, comment="客户端User-Agent"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, comment="过期时间"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True, comment="撤销时间"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_refresh_tokens_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_tokens_token_hash")),
    )
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_token_hash"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index(op.f("ix_users_invite_code"), table_name="users")
    op.drop_index(op.f("ix_users_account"), table_name="users")
    op.drop_table("users")
