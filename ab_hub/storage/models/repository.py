"""Repository ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ab_hub.storage.models.base import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    github_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    owner: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(32), default="public")
    default_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    html_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    clone_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_fork: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # relationships
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    branches = relationship("Branch", back_populates="repository", cascade="all, delete-orphan")
    technologies = relationship(
        "RepositoryTechnology", back_populates="repository", cascade="all, delete-orphan"
    )
    dependencies = relationship(
        "Dependency", back_populates="repository", cascade="all, delete-orphan"
    )
    activity_snapshots = relationship(
        "ActivitySnapshot", back_populates="repository", cascade="all, delete-orphan"
    )
    events = relationship(
        "RepositoryEvent", back_populates="repository", cascade="all, delete-orphan"
    )
    vulnerabilities = relationship(
        "Vulnerability", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository {self.full_name}>"
