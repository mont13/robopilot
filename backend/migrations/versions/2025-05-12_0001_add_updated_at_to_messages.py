"""Add updated_at column to chat_messages table

Revision ID: add_updated_at_to_messages
Revises: 54f68ea8a6b5
Create Date: 2025-05-12 00:01:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_updated_at_to_messages"
down_revision = "54f68ea8a6b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add updated_at column to chat_messages table
    op.add_column(
        "chat_messages",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        )
    )


def downgrade() -> None:
    # Drop updated_at column from chat_messages table
    op.drop_column("chat_messages", "updated_at")
