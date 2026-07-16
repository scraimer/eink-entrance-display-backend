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
    Boolean,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
    CheckConstraint,
    text,
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
    in_rotation = Column(Boolean, nullable=False, default=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    # Relationships
    executions = relationship("Execution", back_populates="executor", cascade="all, delete-orphan")
    rankings = relationship("Ranking", back_populates="person", cascade="all, delete-orphan")
    last_executed_chores = relationship(
        "ChoreState", foreign_keys="ChoreState.last_executor_id", back_populates="last_executor"
    )
    fixed_executor_chores = relationship(
        "ChoreState", foreign_keys="ChoreState.fixed_executor_id", back_populates="fixed_executor"
    )


class Chore(Base):
    """Chore definition with frequency."""

    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    frequency_in_weeks = Column(Integer, nullable=False)
    same_person_next_time = Column(Boolean, nullable=False, default=False)
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
    fixed_executor_id = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    next_execution_date = Column(String, nullable=True)  # ISO 8601 date format
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    # Relationships
    chore = relationship("Chore", back_populates="state")
    last_executor = relationship(
        "Person", foreign_keys=[last_executor_id], back_populates="last_executed_chores"
    )
    fixed_executor = relationship(
        "Person", foreign_keys=[fixed_executor_id], back_populates="fixed_executor_chores"
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


class DatedChorePlan(Base):
    """Persisted chore plan snapshot keyed by a target plan date."""

    __tablename__ = "dated_chore_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_date = Column(String, nullable=False, unique=True)  # ISO 8601 date format
    plan_data = Column(Text, nullable=False)  # JSON payload
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_dated_chore_plans_plan_date", "plan_date"),
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

    def migrate_db(self):
        """Apply additive schema migrations for existing databases.

        Safe to call on every startup — each migration is idempotent.
        """
        if "sqlite" not in self.database_url:
            return
        db_path = self.database_url.replace("sqlite:///", "")
        import sqlite3 as _sqlite3
        con = _sqlite3.connect(db_path)
        try:
            existing_cols = {row[1] for row in con.execute("PRAGMA table_info(people)")}
            if "in_rotation" not in existing_cols:
                con.execute(
                    "ALTER TABLE people ADD COLUMN in_rotation INTEGER NOT NULL DEFAULT 1"
                )
                con.commit()

            chore_state_cols = {row[1] for row in con.execute("PRAGMA table_info(chore_state)")}
            if chore_state_cols and "next_executor_id" in chore_state_cols:
                con.execute("PRAGMA foreign_keys=OFF")
                con.execute("BEGIN")
                con.execute(
                    """
                    CREATE TABLE chore_state_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chore_id INTEGER NOT NULL UNIQUE REFERENCES chores(id) ON DELETE CASCADE,
                        last_executor_id INTEGER REFERENCES people(id) ON DELETE SET NULL,
                        last_execution_date TEXT,
                        fixed_executor_id INTEGER REFERENCES people(id) ON DELETE SET NULL,
                        next_execution_date TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                con.execute(
                    """
                    INSERT INTO chore_state_new (
                        id,
                        chore_id,
                        last_executor_id,
                        last_execution_date,
                        fixed_executor_id,
                        next_execution_date,
                        created_at,
                        updated_at
                    )
                    SELECT
                        state.id,
                        state.chore_id,
                        state.last_executor_id,
                        state.last_execution_date,
                        CASE
                            WHEN chores.same_person_next_time = 1 THEN state.next_executor_id
                            ELSE NULL
                        END,
                        state.next_execution_date,
                        state.created_at,
                        state.updated_at
                    FROM chore_state AS state
                    JOIN chores ON chores.id = state.chore_id
                    """
                )
                con.execute("DROP TABLE chore_state")
                con.execute("ALTER TABLE chore_state_new RENAME TO chore_state")
                con.commit()
                con.execute("PRAGMA foreign_keys=ON")

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS dated_chore_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_date TEXT NOT NULL UNIQUE,
                    plan_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS ix_dated_chore_plans_plan_date ON dated_chore_plans(plan_date)"
            )
            con.commit()
        finally:
            con.close()

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
    in_rotation: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ChoreData:
    """Chore data for API responses."""

    id: Optional[int] = None
    name: str = ""
    frequency_in_weeks: int = 1
    same_person_next_time: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ChoreStateData:
    """Chore state data for API responses."""

    id: Optional[int] = None
    chore_id: int = 0
    last_executor_id: Optional[int] = None
    last_execution_date: Optional[str] = None
    fixed_executor_id: Optional[int] = None
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


# Number of days back to look when counting executions for scoring purposes.
# Executions older than this window do not contribute to the execution count.
SCORE_EXECUTION_WINDOW_DAYS = 730  # 2 years

# Maximum number of days since last execution used in the recency term.
# Beyond this cap the recency advantage stops growing.
SCORE_RECENCY_CAP_DAYS = 365


def compute_chore_scores(
    session: Session,
    as_of_date_iso: Optional[str] = None,
) -> list[tuple[int, int, int]]:
    """Compute weighted scores for every in-rotation person and chore pair.

    Only executions within the last SCORE_EXECUTION_WINDOW_DAYS days are counted.
    The recency term is capped at SCORE_RECENCY_CAP_DAYS.

    Returns:
        List of (person_id, chore_id, score) tuples, one row per eligible pair.
    """
    effective_as_of = as_of_date_iso or utc_today_iso()

    query = text(
        f"""
        SELECT
            p.id AS person_id,
            c.id AS chore_id,
            (
                COALESCE(COUNT(e.id), 0) * 1000
                - COALESCE(
                    MIN(
                        CAST(julianday(:as_of_date) - julianday(MAX(e.execution_date)) AS INTEGER),
                        {SCORE_RECENCY_CAP_DAYS}
                    ),
                    {SCORE_RECENCY_CAP_DAYS}
                )
            ) AS score
        FROM people AS p
        CROSS JOIN chores AS c
        LEFT JOIN executions AS e
            ON e.executor_id = p.id
           AND e.chore_id = c.id
           AND julianday(:as_of_date) - julianday(e.execution_date) <= {SCORE_EXECUTION_WINDOW_DAYS}
        WHERE p.in_rotation = 1
        GROUP BY p.id, c.id
        ORDER BY c.id, score ASC, p.ordinal ASC, p.id ASC
        """
    )
    rows = session.execute(query, {"as_of_date": effective_as_of}).all()
    return [(int(row.person_id), int(row.chore_id), int(row.score)) for row in rows]


def get_next_executor_id(session: Session, chore: Chore) -> Optional[int]:
    """Return the next executor for a chore using weighted scores.

    Fixed-executor chores bypass scoring and return their stored fixed executor.
    """
    if chore.same_person_next_time:
        return chore.state.fixed_executor_id if chore.state else None

    chore_scores = [row for row in compute_chore_scores(session) if row[1] == chore.id]
    if not chore_scores:
        return None
    return chore_scores[0][0]


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
