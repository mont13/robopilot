"""Add function_calls table

Revision ID: add_function_calls_table
Revises: add_updated_at_to_messages
Create Date: 2025-05-13 00:01:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_function_calls_table"
down_revision = "add_updated_at_to_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create function_calls table
    op.create_table(
        "function_calls",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("message_id", sa.String(36), nullable=True),
        sa.Column("function_name", sa.String(255), nullable=False),
        sa.Column("arguments", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_function_calls")),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            name=op.f("fk_function_calls_session_id_chat_sessions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["chat_messages.id"],
            name=op.f("fk_function_calls_message_id_chat_messages"),
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    # Drop function_calls table
    op.drop_table("function_calls")
