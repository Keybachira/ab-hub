"""Activity snapshot ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ab_hub.storage.models.base import Base


class ActivitySnapshot(Base):
    __tablename__ = "activity_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    activity_score: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    repository = relationship("Repository", back_populates="activity_snapshots")
