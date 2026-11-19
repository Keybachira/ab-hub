"""Commit ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ab_hub.storage.models.base import Base


class Commit(Base):
    __tablename__ = "commits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    sha: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    committer_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    repository = relationship("Repository", back_populates="commits")
