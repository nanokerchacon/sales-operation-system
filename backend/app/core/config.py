import os


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/sales_operation_system",
)
AUTO_CREATE_SCHEMA = os.getenv("AUTO_CREATE_SCHEMA", "true").strip().lower() == "true"
AUTH_TOKEN_EXPIRE_HOURS = int(os.getenv("AUTH_TOKEN_EXPIRE_HOURS", "24"))
