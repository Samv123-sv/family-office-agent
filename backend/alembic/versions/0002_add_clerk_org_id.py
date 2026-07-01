"""add clerk_org_id to clients

Revision ID: 0002
Revises: 9ec53f6f4f22
Create Date: 2026-06-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "9ec53f6f4f22"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("clerk_org_id", sa.String(), nullable=True))
    op.create_index("ix_clients_clerk_org_id", "clients", ["clerk_org_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_clients_clerk_org_id", table_name="clients")
    op.drop_column("clients", "clerk_org_id")
