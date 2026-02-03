from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_learning_events_text_fields"
down_revision = "0002_tm_core"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("learning_events", sa.Column("source_text", sa.Text()))
    op.add_column("learning_events", sa.Column("target_text", sa.Text()))
    op.add_column("learning_events", sa.Column("source_lang", sa.String(length=16)))
    op.add_column("learning_events", sa.Column("target_lang", sa.String(length=16)))


def downgrade():
    op.drop_column("learning_events", "target_lang")
    op.drop_column("learning_events", "source_lang")
    op.drop_column("learning_events", "target_text")
    op.drop_column("learning_events", "source_text")
