"""add missing columns to optimization_records

Revision ID: add_missing_columns
Revises: 
Create Date: 2025-11-21 11:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_missing_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns exist before adding (works for both SQLite and PostgreSQL)
    # For SQLite, we need to check differently
    conn = op.get_bind()
    
    # Try to add tax_rate column if it doesn't exist
    try:
        op.add_column('optimization_records', sa.Column('tax_rate', sa.Float(), nullable=True))
    except Exception:
        # Column might already exist, which is fine
        pass
    
    # Try to add tax_free_allowance_remaining column if it doesn't exist
    try:
        op.add_column('optimization_records', sa.Column('tax_free_allowance_remaining', sa.Float(), nullable=True))
    except Exception:
        # Column might already exist, which is fine
        pass


def downgrade():
    # Remove columns if they exist
    try:
        op.drop_column('optimization_records', 'tax_free_allowance_remaining')
    except Exception:
        pass
    
    try:
        op.drop_column('optimization_records', 'tax_rate')
    except Exception:
        pass

