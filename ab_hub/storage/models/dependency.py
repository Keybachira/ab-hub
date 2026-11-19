"""Dependency ORM model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ab_hub.storage.models.base import Base


class Dependency(Base):
    __tablename__ = "dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ecosystem: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_file: Mapped[str] = mapped_column(String(255), nullable=False)

    repository = relationship("Repository", back_populates="dependencies")
