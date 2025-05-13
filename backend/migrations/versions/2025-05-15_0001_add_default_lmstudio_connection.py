"""Add default LMStudio connection

Revision ID: add_default_lmstudio_connection
Revises: add_llm_connections_table
Create Date: 2025-05-15 00:01:00.000000

"""

import json
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = "add_default_lmstudio_connection"
down_revision = "add_llm_connections_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Define table structure for inserting data
    llm_connections = table(
        "llm_connections",
        column("id", sa.String),
        column("name", sa.String),
        column("provider", sa.String),
        column("model_name", sa.String),
        column("base_url", sa.String),
        column("api_key", sa.Text),
        column("is_active", sa.Boolean),
        column("config_json", sa.Text),
    )

    # Insert default LMStudio connection
    op.bulk_insert(
        llm_connections,
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Local LM Studio",
                "provider": "lmstudio",
                "model_name": "gemma-3-4b-it-qat",
                "base_url": "http://localhost:1234/v1",
                "api_key": None,
                "is_active": True,
                "config_json": json.dumps(
                    {
                        "temperature": 0.7,
                        "max_tokens": 1000,
                        "timeout": 60,
                        "response_format": {"type": "text"},
                    }
                ),
            }
        ],
    )


def downgrade() -> None:
    # Cannot reliably delete only the default connection
    # as the ID is generated on insertion
    pass
