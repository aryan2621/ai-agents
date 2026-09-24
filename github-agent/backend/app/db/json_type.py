from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# JSON column compatible with PostgreSQL (JSONB) and SQLite (JSON).
json_column = JSON().with_variant(JSONB(), "postgresql")
