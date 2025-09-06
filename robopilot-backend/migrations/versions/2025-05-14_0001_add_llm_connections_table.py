"""Add llm_connections table

Revision ID: add_llm_connections_table
Revises: add_function_calls_table
Create Date: 2025-05-14 00:01:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_llm_connections_table"
down_revision = "add_function_calls_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create llm_connections table
    op.create_table(
        "llm_connections",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("base_url", sa.String(255), nullable=True),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("api_version", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=False, nullable=False),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_llm_connections")),
    )

    # Add an index on is_active to quickly find the active connection
    op.create_index(
        "ix_llm_connections_is_active", "llm_connections", ["is_active"], unique=False
    )


def downgrade() -> None:
    # Drop llm_connections table
    op.drop_index("ix_llm_connections_is_active", table_name="llm_connections")
    op.drop_table("llm_connections")
