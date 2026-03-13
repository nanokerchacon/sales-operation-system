from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260313_02"
down_revision = "20260313_01"
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "invoices", "source_folder"):
        op.add_column("invoices", sa.Column("source_folder", sa.String(), nullable=True))
    if not _has_column(inspector, "invoices", "invoice_type"):
        op.add_column("invoices", sa.Column("invoice_type", sa.String(), nullable=True))
    if not _has_column(inspector, "invoices", "invoice_status"):
        op.add_column("invoices", sa.Column("invoice_status", sa.String(), nullable=True))

    op.execute("UPDATE invoices SET invoice_type = 'standard' WHERE invoice_type IS NULL")
    op.execute("UPDATE invoices SET invoice_status = 'accepted' WHERE invoice_status IS NULL")

    op.execute(
        """
        UPDATE invoices
        SET invoice_type = 'national', invoice_status = 'accepted'
        WHERE UPPER(TRIM(COALESCE(source_folder, ''))) = 'N 2026'
        """
    )
    op.execute(
        """
        UPDATE invoices
        SET invoice_type = 'intracommunity', invoice_status = 'accepted'
        WHERE UPPER(TRIM(COALESCE(source_folder, ''))) = 'IC 2026'
        """
    )
    op.execute(
        """
        UPDATE invoices
        SET invoice_type = 'export', invoice_status = 'accepted'
        WHERE UPPER(TRIM(COALESCE(source_folder, ''))) = 'EX 2026'
        """
    )
    op.execute(
        """
        UPDATE invoices
        SET invoice_type = 'commercial_invoice', invoice_status = 'accepted'
        WHERE UPPER(TRIM(COALESCE(source_folder, ''))) = 'CI 2026'
        """
    )
    op.execute(
        """
        UPDATE invoices
        SET invoice_type = 'electronic', invoice_status = 'pending_acceptance'
        WHERE UPPER(TRIM(COALESCE(source_folder, ''))) IN ('FACE', 'FACEEMIT')
        """
    )
    op.execute(
        """
        UPDATE invoices
        SET invoice_type = 'rectificative', invoice_status = 'rectified_review'
        WHERE UPPER(TRIM(COALESCE(source_folder, ''))) = 'FR 2026'
        """
    )

    op.alter_column("invoices", "invoice_type", existing_type=sa.String(), nullable=False)
    op.alter_column("invoices", "invoice_status", existing_type=sa.String(), nullable=False)

    inspector = sa.inspect(bind)
    if not _has_index(inspector, "invoices", "ix_invoices_source_folder"):
        op.create_index("ix_invoices_source_folder", "invoices", ["source_folder"], unique=False)
    if not _has_index(inspector, "invoices", "ix_invoices_invoice_status"):
        op.create_index("ix_invoices_invoice_status", "invoices", ["invoice_status"], unique=False)



def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "invoices", "ix_invoices_invoice_status"):
        op.drop_index("ix_invoices_invoice_status", table_name="invoices")
    if _has_index(inspector, "invoices", "ix_invoices_source_folder"):
        op.drop_index("ix_invoices_source_folder", table_name="invoices")

    inspector = sa.inspect(bind)
    for column_name in ["invoice_status", "invoice_type", "source_folder"]:
        if _has_column(inspector, "invoices", column_name):
            op.drop_column("invoices", column_name)
