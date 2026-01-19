"""Add document category field

Revision ID: 002
Revises: 001
Create Date: 2024-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the category enum type
    op.execute("CREATE TYPE documentcategory AS ENUM ('regular', 'case_law', 'regulation', 'template')")

    # Add the category column with default value
    op.add_column(
        'documents',
        sa.Column(
            'category',
            sa.Enum('regular', 'case_law', 'regulation', 'template', name='documentcategory'),
            nullable=False,
            server_default='regular'
        )
    )

    # Create index for category filtering
    op.create_index('ix_documents_category', 'documents', ['category'])


def downgrade() -> None:
    op.drop_index('ix_documents_category')
    op.drop_column('documents', 'category')
    op.execute('DROP TYPE documentcategory')
