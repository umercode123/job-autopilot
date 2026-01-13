"""Add new job fields for Apify data

Revision ID: add_apify_fields
Revises: 
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_apify_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add new columns to jobs table"""
    
    # Date fields
    op.add_column('jobs', sa.Column('expiration_date', sa.DateTime(), nullable=True))
    op.add_column('jobs', sa.Column('job_age', sa.String(), nullable=True))
    
    # URLs
    op.add_column('jobs', sa.Column('apply_url', sa.String(), nullable=True))
    op.add_column('jobs', sa.Column('company_url', sa.String(), nullable=True))
    op.add_column('jobs', sa.Column('company_logo_url', sa.String(), nullable=True))
    op.add_column('jobs', sa.Column('header_image_url', sa.String(), nullable=True))
    
    # Job details
    op.add_column('jobs', sa.Column('job_type', sa.String(), nullable=True))
    op.add_column('jobs', sa.Column('occupation', sa.String(), nullable=True))
    op.add_column('jobs', sa.Column('benefits', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('rating', sa.String(), nullable=True))


def downgrade():
    """Remove new columns from jobs table"""
    
    op.drop_column('jobs', 'rating')
    op.drop_column('jobs', 'benefits')
    op.drop_column('jobs', 'occupation')
    op.drop_column('jobs', 'job_type')
    op.drop_column('jobs', 'header_image_url')
    op.drop_column('jobs', 'company_logo_url')
    op.drop_column('jobs', 'company_url')
    op.drop_column('jobs', 'apply_url')
    op.drop_column('jobs', 'job_age')
    op.drop_column('jobs', 'expiration_date')
