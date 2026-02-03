from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.models.base import Base


class TMCategory(Base):
    __tablename__ = "tm_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class GlossaryEntry(Base):
    __tablename__ = "glossary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_lang: Mapped[str] = mapped_column(String(16), nullable=False)
    target_lang: Mapped[str] = mapped_column(String(16), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    category_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    domain: Mapped[Optional[str]] = mapped_column(String(64))
    category: Mapped[Optional[str]] = mapped_column(String(64))
    scope_type: Mapped[str] = mapped_column(String(16), default="project")
    scope_id: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="active")
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    overwrite_count: Mapped[int] = mapped_column(Integer, default=0)
    last_hit_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class TMEntry(Base):
    __tablename__ = "tm"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_lang: Mapped[str] = mapped_column(String(16), nullable=False)
    target_lang: Mapped[str] = mapped_column(String(16), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_text: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    domain: Mapped[Optional[str]] = mapped_column(String(64))
    category: Mapped[Optional[str]] = mapped_column(String(64))
    scope_type: Mapped[str] = mapped_column(String(16), default="project")
    scope_id: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="active")
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    overwrite_count: Mapped[int] = mapped_column(Integer, default=0)
    last_hit_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class TermFeedback(Base):
    __tablename__ = "term_feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_lang: Mapped[Optional[str]] = mapped_column(String(16))
    target_lang: Mapped[Optional[str]] = mapped_column(String(16))
    correction_count: Mapped[int] = mapped_column(Integer, default=1)
    last_corrected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
