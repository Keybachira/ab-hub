"""Technology related ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ab_hub.storage.models.base import Base


class Technology(Base):
    __tablename__ = "technologies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="other")

    repository_links = relationship("RepositoryTechnology", back_populates="technology")


class RepositoryTechnology(Base):
    __tablename__ = "repository_technologies"
    __table_args__ = (UniqueConstraint("repository_id", "technology_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    technology_id: Mapped[int] = mapped_column(ForeignKey("technologies.id"), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    detection_method: Mapped[str] = mapped_column(String(64), default="inferred")
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    repository = relationship("Repository", back_populates="technologies")
    technology = relationship("Technology", back_populates="repository_links")
