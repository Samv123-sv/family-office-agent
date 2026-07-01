"""add alerts table

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("company_id", sa.UUID(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_client_id", "alerts", ["client_id"])
    op.create_index("ix_alerts_sent_at", "alerts", ["sent_at"])


def downgrade() -> None:
    op.drop_index("ix_alerts_sent_at", table_name="alerts")
    op.drop_index("ix_alerts_client_id", table_name="alerts")
    op.drop_table("alerts")
