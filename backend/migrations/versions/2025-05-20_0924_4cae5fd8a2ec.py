"""Update function_calls table to match model

Revision ID: 4cae5fd8a2ec
Revises: add_ollama_connection
Create Date: 2025-05-20 09:24:02.447046

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4cae5fd8a2ec'
down_revision = 'add_ollama_connection'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Modify message_id column to be non-nullable
    op.alter_column('function_calls', 'message_id',
               existing_type=sa.String(36),
               nullable=False)


def downgrade() -> None:
    # Revert message_id column to be nullable
    op.alter_column('function_calls', 'message_id',
               existing_type=sa.String(36),
               nullable=True)
