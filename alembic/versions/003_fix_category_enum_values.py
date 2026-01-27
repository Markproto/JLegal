"""Fix documentcategory enum values to uppercase

Revision ID: 003
Revises: 002
Create Date: 2024-01-20

"""
from typing import Sequence, Union

from alembic import op

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # If the database was created with the old migration (lowercase values),
    # rename them to uppercase to match SQLAlchemy's default enum name behavior.
    # This is idempotent: if values are already uppercase (fresh deploy), the
    # DO block simply does nothing.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'regular'
                AND enumtypid = 'documentcategory'::regtype
            ) THEN
                ALTER TYPE documentcategory RENAME VALUE 'regular' TO 'REGULAR';
                ALTER TYPE documentcategory RENAME VALUE 'case_law' TO 'CASE_LAW';
                ALTER TYPE documentcategory RENAME VALUE 'regulation' TO 'REGULATION';
                ALTER TYPE documentcategory RENAME VALUE 'template' TO 'TEMPLATE';
            END IF;
        END$$;
    """)

    # Update the default value to uppercase if it was lowercase
    op.execute("""
        ALTER TABLE documents ALTER COLUMN category SET DEFAULT 'REGULAR';
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'REGULAR'
                AND enumtypid = 'documentcategory'::regtype
            ) THEN
                ALTER TYPE documentcategory RENAME VALUE 'REGULAR' TO 'regular';
                ALTER TYPE documentcategory RENAME VALUE 'CASE_LAW' TO 'case_law';
                ALTER TYPE documentcategory RENAME VALUE 'REGULATION' TO 'regulation';
                ALTER TYPE documentcategory RENAME VALUE 'TEMPLATE' TO 'template';
            END IF;
        END$$;
    """)

    op.execute("""
        ALTER TABLE documents ALTER COLUMN category SET DEFAULT 'regular';
    """)
