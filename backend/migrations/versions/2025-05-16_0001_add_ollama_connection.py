"""Add default Ollama connection

Revision ID: add_ollama_connection
Revises: add_default_lmstudio_connection
Create Date: 2025-05-16 00:01:00.000000

"""

import json
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = "add_ollama_connection"
down_revision = "add_default_lmstudio_connection"
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

    # Insert default Ollama connection
    op.bulk_insert(
        llm_connections,
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Local Ollama",
                "provider": "ollama",
                "model_name": "mistral",  # Default model
                "base_url": "http://host.docker.internal:11434/v1",
                "api_key": None,
                "is_active": False,  # LM Studio is active by default
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
    # Cannot reliably delete only the Ollama connection
    # as the ID is generated on insertion
    pass
