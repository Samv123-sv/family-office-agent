"""add documents table

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("company_id", sa.UUID(), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_client_id", "documents", ["client_id"])
    op.create_index("ix_documents_company_id", "documents", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_company_id", table_name="documents")
    op.drop_index("ix_documents_client_id", table_name="documents")
    op.drop_table("documents")
