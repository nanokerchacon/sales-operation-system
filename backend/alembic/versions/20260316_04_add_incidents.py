from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260316_04"
down_revision = "20260316_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("delivery_id", sa.Integer(), sa.ForeignKey("delivery_notes.id"), nullable=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("incident_number", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False, server_default="otro"),
        sa.Column("status", sa.String(), nullable=False, server_default="abierta"),
        sa.Column("priority", sa.String(), nullable=False, server_default="media"),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_incidents_client_id", "incidents", ["client_id"], unique=False)
    op.create_index("ix_incidents_order_id", "incidents", ["order_id"], unique=False)
    op.create_index("ix_incidents_delivery_id", "incidents", ["delivery_id"], unique=False)
    op.create_index("ix_incidents_invoice_id", "incidents", ["invoice_id"], unique=False)
    op.create_index("ix_incidents_incident_number", "incidents", ["incident_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_incidents_incident_number", table_name="incidents")
    op.drop_index("ix_incidents_invoice_id", table_name="incidents")
    op.drop_index("ix_incidents_delivery_id", table_name="incidents")
    op.drop_index("ix_incidents_order_id", table_name="incidents")
    op.drop_index("ix_incidents_client_id", table_name="incidents")
    op.drop_table("incidents")
