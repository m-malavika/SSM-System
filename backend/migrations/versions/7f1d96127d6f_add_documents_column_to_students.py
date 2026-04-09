"""add_documents_column_to_students

Revision ID: 7f1d96127d6f
Revises: 079e66de2321
Create Date: 2025-12-30 12:10:04.070140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '7f1d96127d6f'
down_revision: Union[str, None] = '079e66de2321'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('students', sa.Column('documents', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('students', 'documents')
