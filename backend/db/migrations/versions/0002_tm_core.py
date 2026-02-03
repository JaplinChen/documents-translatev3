from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_tm_core"
down_revision = "0001_auto_learning"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tm_categories",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "glossary",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("source_lang", sa.String(length=16), nullable=False),
        sa.Column("target_lang", sa.String(length=16), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("target_text", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("category_id", sa.BigInteger()),
        sa.Column("domain", sa.String(length=64)),
        sa.Column("category", sa.String(length=64)),
        sa.Column("scope_type", sa.String(length=16), server_default="project"),
        sa.Column("scope_id", sa.String(length=64)),
        sa.Column("status", sa.String(length=16), server_default="active"),
        sa.Column("hit_count", sa.Integer(), server_default="0"),
        sa.Column("overwrite_count", sa.Integer(), server_default="0"),
        sa.Column("last_hit_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "tm",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("source_lang", sa.String(length=16), nullable=False),
        sa.Column("target_lang", sa.String(length=16), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("target_text", sa.Text(), nullable=False),
        sa.Column("category_id", sa.BigInteger()),
        sa.Column("domain", sa.String(length=64)),
        sa.Column("category", sa.String(length=64)),
        sa.Column("scope_type", sa.String(length=16), server_default="project"),
        sa.Column("scope_id", sa.String(length=64)),
        sa.Column("status", sa.String(length=16), server_default="active"),
        sa.Column("hit_count", sa.Integer(), server_default="0"),
        sa.Column("overwrite_count", sa.Integer(), server_default="0"),
        sa.Column("last_hit_at", sa.DateTime(timezone=True)),
        sa.Column("hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "term_feedback",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("target_text", sa.Text(), nullable=False),
        sa.Column("source_lang", sa.String(length=16)),
        sa.Column("target_lang", sa.String(length=16)),
        sa.Column("correction_count", sa.Integer(), server_default="1"),
        sa.Column("last_corrected_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_index(
        "idx_glossary_unique",
        "glossary",
        ["source_lang", "target_lang", "source_text"],
        unique=True,
    )
    op.create_index("idx_glossary_category", "glossary", ["category_id"])
    op.create_index("idx_glossary_scope", "glossary", ["scope_type", "scope_id"])
    op.create_index("idx_tm_category", "tm", ["category_id"])
    op.create_index("idx_tm_scope", "tm", ["scope_type", "scope_id"])
    op.create_index(
        "idx_term_feedback_unique",
        "term_feedback",
        ["source_text", "target_text", "source_lang", "target_lang"],
        unique=True,
    )


def downgrade():
    op.drop_index("idx_term_feedback_unique", table_name="term_feedback")
    op.drop_index("idx_tm_scope", table_name="tm")
    op.drop_index("idx_tm_category", table_name="tm")
    op.drop_index("idx_glossary_scope", table_name="glossary")
    op.drop_index("idx_glossary_category", table_name="glossary")
    op.drop_index("idx_glossary_unique", table_name="glossary")
    op.drop_table("term_feedback")
    op.drop_table("tm")
    op.drop_table("glossary")
    op.drop_table("tm_categories")
