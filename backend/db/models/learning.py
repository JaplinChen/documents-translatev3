from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.models.base import Base


class LearningCandidate(Base):
    __tablename__ = "learning_candidates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_lang: Mapped[str] = mapped_column(String(16), nullable=False)
    target_lang: Mapped[str] = mapped_column(String(16), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(64))
    category: Mapped[Optional[str]] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=0)
    score: Mapped[float] = mapped_column(Numeric(4, 3), default=0)
    freq_norm: Mapped[float] = mapped_column(Numeric(4, 3), default=0)
    context_similarity: Mapped[float] = mapped_column(Numeric(4, 3), default=0)
    alignment_quality: Mapped[float] = mapped_column(Numeric(4, 3), default=0)
    recency: Mapped[float] = mapped_column(Numeric(4, 3), default=0)
    min_count: Mapped[int] = mapped_column(Integer, default=3)
    min_unique_users: Mapped[int] = mapped_column(Integer, default=2)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    overwrite_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="staging")
    scope_type: Mapped[str] = mapped_column(String(16), default="project")
    scope_id: Mapped[Optional[str]] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(16), default="auto")
    last_hit_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LearningEvent(Base):
    __tablename__ = "learning_events"

    event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(16), nullable=False)
    scope_id: Mapped[Optional[str]] = mapped_column(String(64))
    source_ref: Mapped[Optional[str]] = mapped_column(String(128))
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_id: Mapped[Optional[str]] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    source_text: Mapped[Optional[str]] = mapped_column(Text)
    target_text: Mapped[Optional[str]] = mapped_column(Text)
    source_lang: Mapped[Optional[str]] = mapped_column(String(16))
    target_lang: Mapped[Optional[str]] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=0)
    before_payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    after_payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LearningStat(Base):
    __tablename__ = "learning_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    scope_type: Mapped[str] = mapped_column(String(16), nullable=False)
    scope_id: Mapped[Optional[str]] = mapped_column(String(64))
    tm_hit_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    glossary_hit_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    overwrite_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    auto_promotion_error_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    wrong_suggestion_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
