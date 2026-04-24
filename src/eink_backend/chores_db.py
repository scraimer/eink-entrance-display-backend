"""
Chores database models and schema for SQLite backend.

This module defines:
- SQLAlchemy ORM models for all chores-related tables
- Database schema initialization and migrations
- Audit logging infrastructure
"""

from datetime import datetime, date
from typing import Optional, List
import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, asdict
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

Base = declarative_base()


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================


class Person(Base):
    """Household member who can perform chores."""

    __tablename__ = "people"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    ordinal = Column(Integer, nullable=False)
    avatar = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    # Relationships
    executions = relationship("Execution", back_populates="executor", cascade="all, delete-orphan")
    rankings = relationship("Ranking", back_populates="person", cascade="all, delete-orphan")
    last_executed_chores = relationship(
        "ChoreState", foreign_keys="ChoreState.last_executor_id", back_populates="last_executor"
    )
    next_executor_chores = relationship(
        "ChoreState", foreign_keys="ChoreState.next_executor_id", back_populates="next_executor"
    )


class Chore(Base):
    """Chore definition with frequency."""

    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    frequency_in_weeks = Column(Integer, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    __table_args__ = (CheckConstraint("frequency_in_weeks >= 1"),)

    # Relationships
    state = relationship("ChoreState", back_populates="chore", uselist=False, cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="chore", cascade="all, delete-orphan")
    rankings = relationship("Ranking", back_populates="chore", cascade="all, delete-orphan")


class ChoreState(Base):
    """Current state of a chore (last execution, next scheduled)."""

    __tablename__ = "chore_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chore_id = Column(Integer, ForeignKey("chores.id", ondelete="CASCADE"), nullable=False, unique=True)
    last_executor_id = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    last_execution_date = Column(String, nullable=True)  # ISO 8601 date format
    next_executor_id = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    next_execution_date = Column(String, nullable=True)  # ISO 8601 date format
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    # Relationships
    chore = relationship("Chore", back_populates="state")
    last_executor = relationship(
        "Person", foreign_keys=[last_executor_id], back_populates="last_executed_chores"
    )
    next_executor = relationship(
        "Person", foreign_keys=[next_executor_id], back_populates="next_executor_chores"
    )


class Execution(Base):
    """Historical record of a chore execution."""

    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chore_id = Column(Integer, ForeignKey("chores.id", ondelete="CASCADE"), nullable=False)
    executor_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    execution_date = Column(String, nullable=False)  # ISO 8601 date format
    created_at = Column(String, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_executions_chore_date", "chore_id", "execution_date"),
        Index("ix_executions_executor", "executor_id"),
    )

    # Relationships
    chore = relationship("Chore", back_populates="executions")
    executor = relationship("Person", back_populates="executions")


class Ranking(Base):
    """Person's preference rating (1-10) for a chore."""

    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    chore_id = Column(Integer, ForeignKey("chores.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("person_id", "chore_id"),
        CheckConstraint("rating >= 1 AND rating <= 10"),
        Index("ix_rankings_chore", "chore_id"),
    )

    # Relationships
    person = relationship("Person", back_populates="rankings")
    chore = relationship("Chore", back_populates="rankings")


class AuditLogEntry(Base):
    """Audit log of all changes to chores-related tables."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String, nullable=False)
    operation = Column(String, nullable=False)  # INSERT, UPDATE, DELETE
    record_id = Column(Integer, nullable=False)
    before_values = Column(Text, nullable=True)  # JSON string
    after_values = Column(Text, nullable=True)  # JSON string
    changed_at = Column(String, nullable=False)  # ISO 8601 timestamp
    changed_by = Column(String, nullable=True)  # api, migration, auto

    __table_args__ = (
        Index("ix_audit_table_record", "table_name", "record_id"),
        Index("ix_audit_changed_at", "changed_at"),
    )


# ============================================================================
# Database Initialization
# ============================================================================


class ChoresDatabase:
    """Database connection and session management for chores."""

    def __init__(self, database_url: str = "sqlite:////app/data/chores.sqlite"):
        """Initialize database connection.

        Args:
            database_url: SQLAlchemy database URL. Defaults to /app/data/chores.sqlite
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def close(self):
        """Close the database connection."""
        self.engine.dispose()


# ============================================================================
# Dataclass Models (for API responses)
# ============================================================================


@dataclass
class PersonData:
    """Person data for API responses."""

    id: Optional[int] = None
    name: str = ""
    ordinal: int = 0
    avatar: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ChoreData:
    """Chore data for API responses."""

    id: Optional[int] = None
    name: str = ""
    frequency_in_weeks: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ChoreStateData:
    """Chore state data for API responses."""

    id: Optional[int] = None
    chore_id: int = 0
    last_executor_id: Optional[int] = None
    last_execution_date: Optional[str] = None
    next_executor_id: Optional[int] = None
    next_execution_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ExecutionData:
    """Execution data for API responses."""

    id: Optional[int] = None
    chore_id: int = 0
    executor_id: int = 0
    execution_date: str = ""
    created_at: Optional[str] = None


@dataclass
class RankingData:
    """Ranking data for API responses."""

    id: Optional[int] = None
    person_id: int = 0
    chore_id: int = 0
    rating: int = 5
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class AuditLogEntryData:
    """Audit log entry data for API responses."""

    id: Optional[int] = None
    table_name: str = ""
    operation: str = ""
    record_id: int = 0
    before_values: Optional[str] = None
    after_values: Optional[str] = None
    changed_at: str = ""
    changed_by: Optional[str] = None


# ============================================================================
# Utility Functions
# ============================================================================


def serialize_to_json(data: dict) -> str:
    """Serialize a dictionary to JSON string for audit log.

    Args:
        data: Dictionary to serialize

    Returns:
        JSON string representation
    """

    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return super().default(obj)

    return json.dumps(data, cls=DateTimeEncoder)


def utc_now_iso() -> str:
    """Get current UTC time in ISO 8601 format.

    Returns:
        ISO 8601 formatted UTC timestamp
    """
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_today_iso() -> str:
    """Get current UTC date in ISO 8601 format.

    Returns:
        ISO 8601 formatted UTC date (YYYY-MM-DD)
    """
    return date.today().isoformat()
