"""add column comments

Revision ID: 20260808_0002
Revises: 20260806_0001
Create Date: 2026-08-08 08:15:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260808_0002"
down_revision: str | None = "20260806_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMN_COMMENTS = {
    "users": {
        "id": "用户ID",
        "account": "登录账号",
        "password_hash": "密码哈希",
        "nickname": "用户昵称",
        "birth_year": "出生年份",
        "avatar_url": "头像地址",
        "invite_code": "邀请码",
        "accepted_terms": "是否同意条款",
        "status": "账号状态",
        "last_login_at": "最后登录日期",
        "created_at": "创建时间",
        "updated_at": "更新时间",
    },
    "refresh_tokens": {
        "id": "刷新令牌ID",
        "user_id": "所属用户ID",
        "token_hash": "刷新令牌哈希",
        "user_agent": "客户端User-Agent",
        "expires_at": "过期时间",
        "revoked_at": "撤销时间",
        "created_at": "创建时间",
        "updated_at": "更新时间",
    },
}


def upgrade() -> None:
    for table_name, columns in COLUMN_COMMENTS.items():
        for column_name, comment in columns.items():
            op.execute(f"COMMENT ON COLUMN {table_name}.{column_name} IS '{comment}'")


def downgrade() -> None:
    for table_name, columns in COLUMN_COMMENTS.items():
        for column_name in columns:
            op.execute(f"COMMENT ON COLUMN {table_name}.{column_name} IS NULL")
