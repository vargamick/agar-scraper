"""Add folder_name field to jobs table

Revision ID: 001
Revises:
Create Date: 2025-01-13 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add folder_name column to jobs table."""
    op.add_column('jobs', sa.Column('folder_name', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_jobs_folder_name'), 'jobs', ['folder_name'], unique=False)


def downgrade():
    """Remove folder_name column from jobs table."""
    op.drop_index(op.f('ix_jobs_folder_name'), table_name='jobs')
    op.drop_column('jobs', 'folder_name')
