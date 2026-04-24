"""
Audit logging infrastructure for chores database.

This module provides:
- Wrapper functions for database operations with automatic audit logging
- Decorators and context managers for transparent audit tracking
- Cleanup utilities for managing audit log retention
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .chores_db import (
    AuditLogEntry,
    serialize_to_json,
    utc_now_iso,
)


# ============================================================================
# Audit Logging Core Functions
# ============================================================================


def audit_insert(
    session: Session,
    table_name: str,
    record_id: int,
    after_values: Dict[str, Any],
    changed_by: str = "api",
):
    """Log an INSERT operation to the audit log.

    Args:
        session: SQLAlchemy session
        table_name: Name of the table being modified
        record_id: ID of the record in the source table
        after_values: Dictionary of all column values after insertion
        changed_by: Identifier of who made the change (api, migration, auto)
    """
    audit_entry = AuditLogEntry(
        table_name=table_name,
        operation="INSERT",
        record_id=record_id,
        before_values=None,
        after_values=serialize_to_json(after_values),
        changed_at=utc_now_iso(),
        changed_by=changed_by,
    )
    session.add(audit_entry)


def audit_update(
    session: Session,
    table_name: str,
    record_id: int,
    before_values: Dict[str, Any],
    after_values: Dict[str, Any],
    changed_by: str = "api",
):
    """Log an UPDATE operation to the audit log.

    Args:
        session: SQLAlchemy session
        table_name: Name of the table being modified
        record_id: ID of the record in the source table
        before_values: Dictionary of all column values before update
        after_values: Dictionary of all column values after update
        changed_by: Identifier of who made the change (api, migration, auto)
    """
    audit_entry = AuditLogEntry(
        table_name=table_name,
        operation="UPDATE",
        record_id=record_id,
        before_values=serialize_to_json(before_values),
        after_values=serialize_to_json(after_values),
        changed_at=utc_now_iso(),
        changed_by=changed_by,
    )
    session.add(audit_entry)


def audit_delete(
    session: Session,
    table_name: str,
    record_id: int,
    before_values: Dict[str, Any],
    changed_by: str = "api",
):
    """Log a DELETE operation to the audit log.

    Args:
        session: SQLAlchemy session
        table_name: Name of the table being modified
        record_id: ID of the record in the source table
        before_values: Dictionary of all column values before deletion
        changed_by: Identifier of who made the change (api, migration, auto)
    """
    audit_entry = AuditLogEntry(
        table_name=table_name,
        operation="DELETE",
        record_id=record_id,
        before_values=serialize_to_json(before_values),
        after_values=None,
        changed_at=utc_now_iso(),
        changed_by=changed_by,
    )
    session.add(audit_entry)


# ============================================================================
# Audit Log Cleanup
# ============================================================================


def cleanup_audit_log(session: Session, days_to_keep: int = 365) -> int:
    """Delete audit log entries older than the specified number of days.

    This function:
    - Runs non-blocking (single query)
    - Deletes records older than now - days_to_keep
    - Returns count of deleted records

    Args:
        session: SQLAlchemy session
        days_to_keep: Number of days to retain (default 365)

    Returns:
        Number of audit log entries deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    cutoff_iso = cutoff_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Delete audit log entries older than cutoff date
    deleted_count = session.query(AuditLogEntry).filter(
        AuditLogEntry.changed_at < cutoff_iso
    ).delete()

    session.commit()
    return deleted_count


# ============================================================================
# Audit Log Querying
# ============================================================================


def query_audit_log(
    session: Session,
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    operation: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 1000,
) -> list:
    """Query audit log with optional filtering.

    Args:
        session: SQLAlchemy session
        table_name: Filter by table name (optional)
        record_id: Filter by record ID (optional)
        operation: Filter by operation (INSERT, UPDATE, DELETE, optional)
        since: Filter to entries on or after this ISO 8601 timestamp (optional)
        until: Filter to entries on or before this ISO 8601 timestamp (optional)
        limit: Maximum number of results (default 1000)

    Returns:
        List of AuditLogEntry objects, limited to max 1000 records

    Raises:
        ValueError: If result set would exceed limit
    """
    query = session.query(AuditLogEntry)

    if table_name:
        query = query.filter(AuditLogEntry.table_name == table_name)

    if record_id is not None:
        query = query.filter(AuditLogEntry.record_id == record_id)

    if operation:
        query = query.filter(AuditLogEntry.operation == operation)

    if since:
        query = query.filter(AuditLogEntry.changed_at >= since)

    if until:
        query = query.filter(AuditLogEntry.changed_at <= until)

    # Check if result would exceed limit
    count = query.count()
    if count > limit:
        raise ValueError(
            f"Result set exceeds maximum limit of {limit} records. "
            f"Use more specific filters to narrow your query."
        )

    return query.order_by(AuditLogEntry.changed_at.desc()).all()


# ============================================================================
# Audit Log Analysis
# ============================================================================


def get_record_history(
    session: Session,
    table_name: str,
    record_id: int,
) -> list:
    """Get complete change history for a specific record.

    Args:
        session: SQLAlchemy session
        table_name: Name of the table
        record_id: ID of the record

    Returns:
        List of AuditLogEntry objects in chronological order (oldest first)
    """
    return (
        session.query(AuditLogEntry)
        .filter(
            (AuditLogEntry.table_name == table_name)
            & (AuditLogEntry.record_id == record_id)
        )
        .order_by(AuditLogEntry.changed_at.asc())
        .all()
    )


def get_record_before_values(
    session: Session,
    table_name: str,
    record_id: int,
) -> Optional[Dict[str, Any]]:
    """Get the last known state of a deleted record (for recovery).

    Args:
        session: SQLAlchemy session
        table_name: Name of the table
        record_id: ID of the record

    Returns:
        Dictionary of column values from the last before-deletion state,
        or None if record has not been deleted
    """
    deletion = (
        session.query(AuditLogEntry)
        .filter(
            (AuditLogEntry.table_name == table_name)
            & (AuditLogEntry.record_id == record_id)
            & (AuditLogEntry.operation == "DELETE")
        )
        .order_by(AuditLogEntry.changed_at.desc())
        .first()
    )

    if deletion and deletion.before_values:
        return json.loads(deletion.before_values)

    return None
