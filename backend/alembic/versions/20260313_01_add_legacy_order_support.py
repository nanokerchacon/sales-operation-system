from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260313_01"
down_revision = None
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "clients", "legacy_code"):
        op.add_column("clients", sa.Column("legacy_code", sa.String(), nullable=True))
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_clients_legacy_code
        ON clients (legacy_code)
        WHERE legacy_code IS NOT NULL
        """
    )

    inspector = sa.inspect(bind)
    if not _has_column(inspector, "products", "legacy_code"):
        op.add_column("products", sa.Column("legacy_code", sa.String(), nullable=True))
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_products_legacy_code
        ON products (legacy_code)
        WHERE legacy_code IS NOT NULL
        """
    )

    inspector = sa.inspect(bind)
    order_columns = {
        "series": sa.Column("series", sa.String(), nullable=True),
        "order_number": sa.Column("order_number", sa.String(), nullable=True),
        "legacy_client_code": sa.Column("legacy_client_code", sa.String(), nullable=True),
        "client_name_snapshot": sa.Column("client_name_snapshot", sa.String(), nullable=True),
        "notes": sa.Column("notes", sa.String(), nullable=True),
        "source": sa.Column("source", sa.String(), nullable=True, server_default="erp"),
        "subtotal": sa.Column("subtotal", sa.Float(), nullable=True),
        "tax_amount": sa.Column("tax_amount", sa.Float(), nullable=True),
        "total_amount": sa.Column("total_amount", sa.Float(), nullable=True),
    }
    for column_name, column in order_columns.items():
        if not _has_column(inspector, "orders", column_name):
            op.add_column("orders", column)

    op.execute("UPDATE orders SET source = 'erp' WHERE source IS NULL")
    op.alter_column("orders", "source", existing_type=sa.String(), nullable=False, server_default=None)
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_series ON orders (series)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_order_number ON orders (order_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_legacy_client_code ON orders (legacy_client_code)")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_source_series_number
        ON orders (source, series, order_number)
        """
    )

    inspector = sa.inspect(bind)
    order_item_columns = {
        "line_number": sa.Column("line_number", sa.Integer(), nullable=True),
        "line_type": sa.Column("line_type", sa.String(), nullable=True, server_default="product"),
        "legacy_article_code": sa.Column("legacy_article_code", sa.String(), nullable=True),
        "description": sa.Column("description", sa.String(), nullable=True),
        "line_amount": sa.Column("line_amount", sa.Float(), nullable=True),
    }
    for column_name, column in order_item_columns.items():
        if not _has_column(inspector, "order_items", column_name):
            op.add_column("order_items", column)

    op.alter_column("order_items", "product_id", existing_type=sa.Integer(), nullable=True)
    op.execute("UPDATE order_items SET line_type = 'product' WHERE line_type IS NULL")
    op.alter_column("order_items", "line_type", existing_type=sa.String(), nullable=False, server_default=None)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_order_items_legacy_article_code ON order_items (legacy_article_code)"
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_order_items_order_line_number
        ON order_items (order_id, line_number)
        WHERE line_number IS NOT NULL
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "order_items", "uq_order_items_order_line_number"):
        op.drop_index("uq_order_items_order_line_number", table_name="order_items")
    if _has_index(inspector, "order_items", "ix_order_items_legacy_article_code"):
        op.drop_index("ix_order_items_legacy_article_code", table_name="order_items")

    inspector = sa.inspect(bind)
    for column_name in ["line_amount", "description", "legacy_article_code", "line_type", "line_number"]:
        if _has_column(inspector, "order_items", column_name):
            op.drop_column("order_items", column_name)

    inspector = sa.inspect(bind)
    for index_name in ["uq_orders_source_series_number", "ix_orders_legacy_client_code", "ix_orders_order_number", "ix_orders_series"]:
        if _has_index(inspector, "orders", index_name):
            op.drop_index(index_name, table_name="orders")

    inspector = sa.inspect(bind)
    for column_name in [
        "total_amount",
        "tax_amount",
        "subtotal",
        "source",
        "notes",
        "client_name_snapshot",
        "legacy_client_code",
        "order_number",
        "series",
    ]:
        if _has_column(inspector, "orders", column_name):
            op.drop_column("orders", column_name)

    inspector = sa.inspect(bind)
    if _has_index(inspector, "products", "ix_products_legacy_code"):
        op.drop_index("ix_products_legacy_code", table_name="products")
    if _has_column(inspector, "products", "legacy_code"):
        op.drop_column("products", "legacy_code")

    inspector = sa.inspect(bind)
    if _has_index(inspector, "clients", "ix_clients_legacy_code"):
        op.drop_index("ix_clients_legacy_code", table_name="clients")
    if _has_column(inspector, "clients", "legacy_code"):
        op.drop_column("clients", "legacy_code")
