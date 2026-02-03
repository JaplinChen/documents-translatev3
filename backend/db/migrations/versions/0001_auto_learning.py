from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_auto_learning"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "learning_candidates",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("target_text", sa.Text(), nullable=False),
        sa.Column("source_lang", sa.String(length=16), nullable=False),
        sa.Column("target_lang", sa.String(length=16), nullable=False),
        sa.Column("domain", sa.String(length=64)),
        sa.Column("category", sa.String(length=64)),
        sa.Column("confidence", sa.Numeric(4, 3), server_default="0"),
        sa.Column("score", sa.Numeric(4, 3), server_default="0"),
        sa.Column("freq_norm", sa.Numeric(4, 3), server_default="0"),
        sa.Column("context_similarity", sa.Numeric(4, 3), server_default="0"),
        sa.Column("alignment_quality", sa.Numeric(4, 3), server_default="0"),
        sa.Column("recency", sa.Numeric(4, 3), server_default="0"),
        sa.Column("min_count", sa.Integer(), server_default="3"),
        sa.Column("min_unique_users", sa.Integer(), server_default="2"),
        sa.Column("hit_count", sa.Integer(), server_default="0"),
        sa.Column("overwrite_count", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(length=16), server_default="staging"),
        sa.Column("scope_type", sa.String(length=16), server_default="project"),
        sa.Column("scope_id", sa.String(length=64)),
        sa.Column("source_type", sa.String(length=16), server_default="auto"),
        sa.Column("last_hit_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "learning_events",
        sa.Column("event_id", sa.BigInteger(), primary_key=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("scope_type", sa.String(length=16), nullable=False),
        sa.Column("scope_id", sa.String(length=64)),
        sa.Column("source_ref", sa.String(length=128)),
        sa.Column("actor_type", sa.String(length=16), nullable=False),
        sa.Column("actor_id", sa.String(length=64)),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.BigInteger()),
        sa.Column("confidence", sa.Numeric(4, 3), server_default="0"),
        sa.Column("before_payload", postgresql.JSONB()),
        sa.Column("after_payload", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "learning_stats",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("scope_type", sa.String(length=16), nullable=False),
        sa.Column("scope_id", sa.String(length=64)),
        sa.Column("tm_hit_rate", sa.Numeric(5, 2)),
        sa.Column("glossary_hit_rate", sa.Numeric(5, 2)),
        sa.Column("overwrite_rate", sa.Numeric(5, 2)),
        sa.Column("auto_promotion_error_rate", sa.Numeric(5, 2)),
        sa.Column("wrong_suggestion_rate", sa.Numeric(5, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_index("idx_lc_scope", "learning_candidates", ["scope_type", "scope_id"])
    op.create_index("idx_lc_lang", "learning_candidates", ["source_lang", "target_lang"])
    op.create_index("idx_lc_status", "learning_candidates", ["status"])
    op.create_index("idx_le_event_type", "learning_events", ["event_type"])
    op.create_index("idx_le_scope", "learning_events", ["scope_type", "scope_id"])
    op.create_index("idx_ls_date", "learning_stats", ["stat_date"])


def downgrade():
    op.drop_index("idx_ls_date", table_name="learning_stats")
    op.drop_index("idx_le_scope", table_name="learning_events")
    op.drop_index("idx_le_event_type", table_name="learning_events")
    op.drop_index("idx_lc_status", table_name="learning_candidates")
    op.drop_index("idx_lc_lang", table_name="learning_candidates")
    op.drop_index("idx_lc_scope", table_name="learning_candidates")
    op.drop_table("learning_stats")
    op.drop_table("learning_events")
    op.drop_table("learning_candidates")
