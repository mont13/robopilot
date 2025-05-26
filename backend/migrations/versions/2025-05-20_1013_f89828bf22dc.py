"""Update function_calls add updated_at column

Revision ID: f89828bf22dc
Revises: 4cae5fd8a2ec
Create Date: 2025-05-20 10:13:55.312939

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f89828bf22dc"
down_revision = "4cae5fd8a2ec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "function_calls",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("function_calls", "updated_at")
