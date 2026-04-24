"""
FastAPI routes for chores management API.

Provides REST endpoints for:
- Chore management (CRUD)
- Person management (CRUD)
- Execution tracking and scheduling
- Rankings management
- Audit log queries
- Summary data for rendering
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session, joinedload, subqueryload

from .chores_db import (
    ChoresDatabase,
    Person,
    Chore,
    ChoreState,
    Execution,
    Ranking,
    AuditLogEntry,
    PersonData,
    ChoreData,
    ChoreStateData,
    ExecutionData,
    RankingData,
    AuditLogEntryData,
    utc_now_iso,
    utc_today_iso,
    serialize_to_json,
)
from .chores_audit import (
    audit_insert,
    audit_update,
    audit_delete,
    query_audit_log,
)


# ============================================================================
# Pydantic Models for API Requests/Responses
# ============================================================================


class PersonRequest(BaseModel):
    """Request body for creating/updating a person."""

    name: str = Field(..., min_length=1, max_length=255)
    ordinal: int = Field(..., ge=1)
    avatar: str = Field(..., min_length=1, max_length=255)


class PersonResponse(BaseModel):
    """Response body for person data."""

    id: int
    name: str
    ordinal: int
    avatar: str
    created_at: str
    updated_at: str


class ChoreRequest(BaseModel):
    """Request body for creating/updating a chore."""

    name: str = Field(..., min_length=1, max_length=255)
    frequency_in_weeks: int = Field(..., ge=1)


class ChoreResponse(BaseModel):
    """Response body for chore data."""

    id: int
    name: str
    frequency_in_weeks: int
    created_at: str
    updated_at: str


class ChoreStateResponse(BaseModel):
    """Response body for chore state data."""

    id: int
    chore_id: int
    last_executor_id: Optional[int] = None
    last_execution_date: Optional[str] = None
    next_executor_id: Optional[int] = None
    next_execution_date: Optional[str] = None
    created_at: str
    updated_at: str


class ExecutionRequest(BaseModel):
    """Request body for performing an execution."""

    chore_id: int = Field(..., ge=1)
    executor_id: int = Field(..., ge=1)


class ExecutionResponse(BaseModel):
    """Response body for execution data."""

    id: int
    chore_id: int
    executor_id: int
    execution_date: str
    created_at: str


class ExecutionNextExecutorRequest(BaseModel):
    """Request body for modifying next executor."""

    chore_id: int = Field(..., ge=1)
    next_executor_id: Optional[int] = Field(None, ge=1)
    next_execution_date: Optional[str] = None

    @validator("next_execution_date")
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class RankingRequest(BaseModel):
    """Request body for creating/updating a ranking."""

    person_id: int = Field(..., ge=1)
    chore_id: int = Field(..., ge=1)
    rating: int = Field(..., ge=1, le=10)


class RankingResponse(BaseModel):
    """Response body for ranking data."""

    id: int
    person_id: int
    chore_id: int
    rating: int
    created_at: str
    updated_at: str


class AuditLogEntryResponse(BaseModel):
    """Response body for audit log entry."""

    id: int
    table_name: str
    operation: str
    record_id: int
    before_values: Optional[str] = None
    after_values: Optional[str] = None
    changed_at: str
    changed_by: Optional[str] = None


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool
    data: Any = None
    error: Optional[str] = None


class ExecutionWithStateResponse(BaseModel):
    """Response body for execution with updated state."""

    execution: ExecutionResponse
    updated_state: ChoreStateResponse


class ChoreWithStateResponse(BaseModel):
    """Chore with current state and rankings."""

    id: int
    name: str
    frequency_in_weeks: int
    state: ChoreStateResponse
    rankings: List[Dict[str, Any]]


class ChoresSummaryResponse(BaseModel):
    """Summary response for all chores with state and rankings."""

    chores: List[ChoreWithStateResponse]


# ============================================================================
# Router Setup
# ============================================================================


def create_chores_router(db: ChoresDatabase) -> APIRouter:
    """Create and configure the chores API router.

    Args:
        db: ChoresDatabase instance for all operations

    Returns:
        Configured FastAPI Router
    """
    router = APIRouter(prefix="/api/v1/chores", tags=["chores"])

    # ========================================================================
    # People Endpoints
    # ========================================================================

    @router.post("/people", response_model=APIResponse, status_code=201)
    def create_person(request: PersonRequest):
        """Create a new person."""
        session = db.get_session()
        try:
            # Check for duplicate name
            existing = session.query(Person).filter(Person.name == request.name).first()
            if existing:
                raise HTTPException(status_code=400, detail="Person name already exists")

            now = utc_now_iso()
            person = Person(
                name=request.name,
                ordinal=request.ordinal,
                avatar=request.avatar,
                created_at=now,
                updated_at=now,
            )
            session.add(person)
            session.flush()  # Get the ID

            # Log to audit
            audit_insert(
                session,
                "people",
                person.id,
                {
                    "id": person.id,
                    "name": person.name,
                    "ordinal": person.ordinal,
                    "avatar": person.avatar,
                    "created_at": person.created_at,
                    "updated_at": person.updated_at,
                },
                changed_by="api",
            )

            session.commit()
            return APIResponse(
                success=True,
                data=PersonResponse(
                    id=person.id,
                    name=person.name,
                    ordinal=person.ordinal,
                    avatar=person.avatar,
                    created_at=person.created_at,
                    updated_at=person.updated_at,
                ),
            )
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    @router.get("/people/{person_id}", response_model=APIResponse)
    def get_person(person_id: int):
        """Get a person by ID."""
        session = db.get_session()
        try:
            person = session.query(Person).filter(Person.id == person_id).first()
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")

            return APIResponse(
                success=True,
                data=PersonResponse(
                    id=person.id,
                    name=person.name,
                    ordinal=person.ordinal,
                    avatar=person.avatar,
                    created_at=person.created_at,
                    updated_at=person.updated_at,
                ),
            )
        finally:
            session.close()

    @router.get("/people", response_model=APIResponse)
    def list_people():
        """List all people sorted by ordinal."""
        session = db.get_session()
        try:
            people = session.query(Person).order_by(Person.ordinal).all()

            if len(people) > 1000:
                raise HTTPException(
                    status_code=400,
                    detail="Result set exceeds maximum limit of 1000 records. "
                    "Use filters to narrow your query.",
                )

            return APIResponse(
                success=True,
                data=[
                    PersonResponse(
                        id=p.id,
                        name=p.name,
                        ordinal=p.ordinal,
                        avatar=p.avatar,
                        created_at=p.created_at,
                        updated_at=p.updated_at,
                    )
                    for p in people
                ],
            )
        finally:
            session.close()

    @router.put("/people/{person_id}", response_model=APIResponse)
    def update_person(person_id: int, request: PersonRequest):
        """Update a person."""
        session = db.get_session()
        try:
            person = session.query(Person).filter(Person.id == person_id).first()
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")

            # Check for duplicate name (if name is being changed)
            if request.name != person.name:
                existing = session.query(Person).filter(Person.name == request.name).first()
                if existing:
                    raise HTTPException(status_code=400, detail="Person name already exists")

            # Capture before values
            before_values = {
                "id": person.id,
                "name": person.name,
                "ordinal": person.ordinal,
                "avatar": person.avatar,
                "created_at": person.created_at,
                "updated_at": person.updated_at,
            }

            # Update
            person.name = request.name
            person.ordinal = request.ordinal
            person.avatar = request.avatar
            person.updated_at = utc_now_iso()

            # Capture after values
            after_values = {
                "id": person.id,
                "name": person.name,
                "ordinal": person.ordinal,
                "avatar": person.avatar,
                "created_at": person.created_at,
                "updated_at": person.updated_at,
            }

            # Log to audit
            audit_update(session, "people", person.id, before_values, after_values, "api")

            session.commit()
            return APIResponse(
                success=True,
                data=PersonResponse(
                    id=person.id,
                    name=person.name,
                    ordinal=person.ordinal,
                    avatar=person.avatar,
                    created_at=person.created_at,
                    updated_at=person.updated_at,
                ),
            )
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    @router.delete("/people/{person_id}", status_code=204)
    def delete_person(person_id: int):
        """Delete a person (CASCADE deletes executions, rankings; updates chore_state)."""
        session = db.get_session()
        try:
            person = session.query(Person).filter(Person.id == person_id).first()
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")

            # Capture before values for person
            before_values = {
                "id": person.id,
                "name": person.name,
                "ordinal": person.ordinal,
                "avatar": person.avatar,
                "created_at": person.created_at,
                "updated_at": person.updated_at,
            }

            # Delete all executions where this person was the executor
            executions = session.query(Execution).filter(
                Execution.executor_id == person_id
            ).all()
            for execution in executions:
                before_exec = {
                    "id": execution.id,
                    "chore_id": execution.chore_id,
                    "executor_id": execution.executor_id,
                    "execution_date": execution.execution_date,
                    "created_at": execution.created_at,
                }
                audit_delete(session, "executions", execution.id, before_exec, "api")
                session.delete(execution)
            
            # Delete all rankings for this person
            rankings = session.query(Ranking).filter(
                Ranking.person_id == person_id
            ).all()
            for ranking in rankings:
                before_rank = {
                    "id": ranking.id,
                    "person_id": ranking.person_id,
                    "chore_id": ranking.chore_id,
                    "rating": ranking.rating,
                    "created_at": ranking.created_at,
                    "updated_at": ranking.updated_at,
                }
                audit_delete(session, "rankings", ranking.id, before_rank, "api")
                session.delete(ranking)
            
            # Update chore_state to set executor_ids to NULL
            chore_states = session.query(ChoreState).filter(
                (ChoreState.last_executor_id == person_id) |
                (ChoreState.next_executor_id == person_id)
            ).all()
            for state in chore_states:
                before_state = {
                    "id": state.id,
                    "chore_id": state.chore_id,
                    "last_executor_id": state.last_executor_id,
                    "last_execution_date": state.last_execution_date,
                    "next_executor_id": state.next_executor_id,
                    "next_execution_date": state.next_execution_date,
                    "created_at": state.created_at,
                    "updated_at": state.updated_at,
                }
                
                # Update the state
                if state.last_executor_id == person_id:
                    state.last_executor_id = None
                if state.next_executor_id == person_id:
                    state.next_executor_id = None
                state.updated_at = utc_now_iso()
                
                after_state = {
                    "id": state.id,
                    "chore_id": state.chore_id,
                    "last_executor_id": state.last_executor_id,
                    "last_execution_date": state.last_execution_date,
                    "next_executor_id": state.next_executor_id,
                    "next_execution_date": state.next_execution_date,
                    "created_at": state.created_at,
                    "updated_at": state.updated_at,
                }
                
                audit_update(session, "chore_state", state.id, before_state, after_state, "api")
            
            # Log person deletion
            audit_delete(session, "people", person.id, before_values, "api")

            # Delete the person
            session.delete(person)
            session.commit()
            return None
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    # ========================================================================
    # Chores Endpoints
    # ========================================================================

    @router.post("/chores", response_model=APIResponse, status_code=201)
    def create_chore(request: ChoreRequest):
        """Create a new chore."""
        session = db.get_session()
        try:
            # Check for duplicate name
            existing = session.query(Chore).filter(Chore.name == request.name).first()
            if existing:
                raise HTTPException(status_code=400, detail="Chore name already exists")

            now = utc_now_iso()
            chore = Chore(
                name=request.name,
                frequency_in_weeks=request.frequency_in_weeks,
                created_at=now,
                updated_at=now,
            )
            session.add(chore)
            session.flush()

            # Create empty chore_state record
            chore_state = ChoreState(
                chore_id=chore.id,
                created_at=now,
                updated_at=now,
            )
            session.add(chore_state)
            session.flush()

            # Log to audit
            audit_insert(
                session,
                "chores",
                chore.id,
                {
                    "id": chore.id,
                    "name": chore.name,
                    "frequency_in_weeks": chore.frequency_in_weeks,
                    "created_at": chore.created_at,
                    "updated_at": chore.updated_at,
                },
                "api",
            )
            audit_insert(
                session,
                "chore_state",
                chore_state.id,
                {
                    "id": chore_state.id,
                    "chore_id": chore_state.chore_id,
                    "last_executor_id": None,
                    "last_execution_date": None,
                    "next_executor_id": None,
                    "next_execution_date": None,
                    "created_at": chore_state.created_at,
                    "updated_at": chore_state.updated_at,
                },
                "api",
            )

            session.commit()
            return APIResponse(
                success=True,
                data=ChoreResponse(
                    id=chore.id,
                    name=chore.name,
                    frequency_in_weeks=chore.frequency_in_weeks,
                    created_at=chore.created_at,
                    updated_at=chore.updated_at,
                ),
            )
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    @router.get("/chores/{chore_id}", response_model=APIResponse)
    def get_chore(chore_id: int):
        """Get a chore by ID."""
        session = db.get_session()
        try:
            chore = session.query(Chore).filter(Chore.id == chore_id).first()
            if not chore:
                raise HTTPException(status_code=404, detail="Chore not found")

            return APIResponse(
                success=True,
                data=ChoreResponse(
                    id=chore.id,
                    name=chore.name,
                    frequency_in_weeks=chore.frequency_in_weeks,
                    created_at=chore.created_at,
                    updated_at=chore.updated_at,
                ),
            )
        finally:
            session.close()

    @router.get("/chores", response_model=APIResponse)
    def list_chores():
        """List all chores."""
        session = db.get_session()
        try:
            chores = session.query(Chore).all()

            if len(chores) > 1000:
                raise HTTPException(
                    status_code=400,
                    detail="Result set exceeds maximum limit of 1000 records. "
                    "Use filters to narrow your query.",
                )

            return APIResponse(
                success=True,
                data=[
                    ChoreResponse(
                        id=c.id,
                        name=c.name,
                        frequency_in_weeks=c.frequency_in_weeks,
                        created_at=c.created_at,
                        updated_at=c.updated_at,
                    )
                    for c in chores
                ],
            )
        finally:
            session.close()

    @router.put("/chores/{chore_id}", response_model=APIResponse)
    def update_chore(chore_id: int, request: ChoreRequest):
        """Update a chore."""
        session = db.get_session()
        try:
            chore = session.query(Chore).filter(Chore.id == chore_id).first()
            if not chore:
                raise HTTPException(status_code=404, detail="Chore not found")

            # Check for duplicate name
            if request.name != chore.name:
                existing = session.query(Chore).filter(Chore.name == request.name).first()
                if existing:
                    raise HTTPException(status_code=400, detail="Chore name already exists")

            # Capture before values
            before_values = {
                "id": chore.id,
                "name": chore.name,
                "frequency_in_weeks": chore.frequency_in_weeks,
                "created_at": chore.created_at,
                "updated_at": chore.updated_at,
            }

            # Update
            chore.name = request.name
            chore.frequency_in_weeks = request.frequency_in_weeks
            chore.updated_at = utc_now_iso()

            # Capture after values
            after_values = {
                "id": chore.id,
                "name": chore.name,
                "frequency_in_weeks": chore.frequency_in_weeks,
                "created_at": chore.created_at,
                "updated_at": chore.updated_at,
            }

            # Log to audit
            audit_update(session, "chores", chore.id, before_values, after_values, "api")

            session.commit()
            return APIResponse(
                success=True,
                data=ChoreResponse(
                    id=chore.id,
                    name=chore.name,
                    frequency_in_weeks=chore.frequency_in_weeks,
                    created_at=chore.created_at,
                    updated_at=chore.updated_at,
                ),
            )
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    @router.delete("/chores/{chore_id}", status_code=204)
    def delete_chore(chore_id: int):
        """Delete a chore (CASCADE deletes state, executions, rankings)."""
        session = db.get_session()
        try:
            chore = session.query(Chore).filter(Chore.id == chore_id).first()
            if not chore:
                raise HTTPException(status_code=404, detail="Chore not found")

            # Capture before values
            before_values = {
                "id": chore.id,
                "name": chore.name,
                "frequency_in_weeks": chore.frequency_in_weeks,
                "created_at": chore.created_at,
                "updated_at": chore.updated_at,
            }

            # Log to audit before deletion
            audit_delete(session, "chores", chore.id, before_values, "api")

            # Delete (CASCADE handles chore_state, executions, rankings)
            session.delete(chore)
            session.commit()
            return None
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    # ========================================================================
    # Execution Endpoints
    # ========================================================================

    @router.post("/executions", response_model=APIResponse, status_code=201)
    def perform_execution(request: ExecutionRequest):
        """Perform a chore execution.

        This operation:
        1. Creates an execution record
        2. Updates chore_state with last executor/date
        3. Calculates next executor/date
        4. Logs all changes to audit_log
        """
        session = db.get_session()
        try:
            # Validate chore exists
            chore = session.query(Chore).filter(Chore.id == request.chore_id).first()
            if not chore:
                raise HTTPException(status_code=404, detail="Chore not found")

            # Validate executor exists
            executor = session.query(Person).filter(Person.id == request.executor_id).first()
            if not executor:
                raise HTTPException(status_code=404, detail="Executor not found")

            now = utc_now_iso()
            today = utc_today_iso()

            # Create execution record
            execution = Execution(
                chore_id=request.chore_id,
                executor_id=request.executor_id,
                execution_date=today,
                created_at=now,
            )
            session.add(execution)
            session.flush()

            # Calculate next executor using round-robin
            all_people = session.query(Person).order_by(Person.ordinal).all()
            if not all_people:
                raise HTTPException(status_code=400, detail="No people available for scheduling")

            # Find next executor
            current_index = 0
            if request.executor_id in [p.id for p in all_people]:
                current_index = next(
                    i for i, p in enumerate(all_people) if p.id == request.executor_id
                )
            next_index = (current_index + 1) % len(all_people)
            next_executor_id = all_people[next_index].id

            # Calculate next execution date
            execution_date = datetime.strptime(today, "%Y-%m-%d").date()
            next_exec_date = execution_date + timedelta(weeks=chore.frequency_in_weeks)
            next_execution_date = next_exec_date.isoformat()

            # Update chore_state
            chore_state = session.query(ChoreState).filter(
                ChoreState.chore_id == request.chore_id
            ).first()
            if not chore_state:
                raise HTTPException(status_code=400, detail="Chore state not found")

            # Capture before values
            before_state = {
                "id": chore_state.id,
                "chore_id": chore_state.chore_id,
                "last_executor_id": chore_state.last_executor_id,
                "last_execution_date": chore_state.last_execution_date,
                "next_executor_id": chore_state.next_executor_id,
                "next_execution_date": chore_state.next_execution_date,
                "created_at": chore_state.created_at,
                "updated_at": chore_state.updated_at,
            }

            # Update state
            chore_state.last_executor_id = request.executor_id
            chore_state.last_execution_date = today
            chore_state.next_executor_id = next_executor_id
            chore_state.next_execution_date = next_execution_date
            chore_state.updated_at = now

            # Capture after values
            after_state = {
                "id": chore_state.id,
                "chore_id": chore_state.chore_id,
                "last_executor_id": chore_state.last_executor_id,
                "last_execution_date": chore_state.last_execution_date,
                "next_executor_id": chore_state.next_executor_id,
                "next_execution_date": chore_state.next_execution_date,
                "created_at": chore_state.created_at,
                "updated_at": chore_state.updated_at,
            }

            # Log to audit
            audit_insert(
                session,
                "executions",
                execution.id,
                {
                    "id": execution.id,
                    "chore_id": execution.chore_id,
                    "executor_id": execution.executor_id,
                    "execution_date": execution.execution_date,
                    "created_at": execution.created_at,
                },
                "api",
            )
            audit_update(session, "chore_state", chore_state.id, before_state, after_state, "auto")

            session.commit()

            return APIResponse(
                success=True,
                data=ExecutionWithStateResponse(
                    execution=ExecutionResponse(
                        id=execution.id,
                        chore_id=execution.chore_id,
                        executor_id=execution.executor_id,
                        execution_date=execution.execution_date,
                        created_at=execution.created_at,
                    ),
                    updated_state=ChoreStateResponse(
                        id=chore_state.id,
                        chore_id=chore_state.chore_id,
                        last_executor_id=chore_state.last_executor_id,
                        last_execution_date=chore_state.last_execution_date,
                        next_executor_id=chore_state.next_executor_id,
                        next_execution_date=chore_state.next_execution_date,
                        created_at=chore_state.created_at,
                        updated_at=chore_state.updated_at,
                    ),
                ),
            )
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    @router.get("/executions", response_model=APIResponse)
    def list_executions(
        chore_id: Optional[int] = None,
        executor_id: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ):
        """List executions with optional filtering."""
        session = db.get_session()
        try:
            query = session.query(Execution)

            if chore_id:
                query = query.filter(Execution.chore_id == chore_id)
            if executor_id:
                query = query.filter(Execution.executor_id == executor_id)
            if since:
                query = query.filter(Execution.execution_date >= since)
            if until:
                query = query.filter(Execution.execution_date <= until)

            executions = query.all()

            if len(executions) > 1000:
                raise HTTPException(
                    status_code=400,
                    detail="Result set exceeds maximum limit of 1000 records. "
                    "Use filters to narrow your query.",
                )

            return APIResponse(
                success=True,
                data=[
                    ExecutionResponse(
                        id=e.id,
                        chore_id=e.chore_id,
                        executor_id=e.executor_id,
                        execution_date=e.execution_date,
                        created_at=e.created_at,
                    )
                    for e in executions
                ],
            )
        finally:
            session.close()

    @router.put("/executions/next-executor", response_model=APIResponse)
    def modify_next_executor(request: ExecutionNextExecutorRequest):
        """Modify next executor and/or next execution date for a chore."""
        session = db.get_session()
        try:
            # Validate chore exists
            chore = session.query(Chore).filter(Chore.id == request.chore_id).first()
            if not chore:
                raise HTTPException(status_code=404, detail="Chore not found")

            # Get chore state
            chore_state = session.query(ChoreState).filter(
                ChoreState.chore_id == request.chore_id
            ).first()
            if not chore_state:
                raise HTTPException(status_code=404, detail="Chore state not found")

            # Validate person if provided
            if request.next_executor_id:
                person = session.query(Person).filter(
                    Person.id == request.next_executor_id
                ).first()
                if not person:
                    raise HTTPException(status_code=404, detail="Person not found")

            # Capture before values
            before_values = {
                "id": chore_state.id,
                "chore_id": chore_state.chore_id,
                "last_executor_id": chore_state.last_executor_id,
                "last_execution_date": chore_state.last_execution_date,
                "next_executor_id": chore_state.next_executor_id,
                "next_execution_date": chore_state.next_execution_date,
                "created_at": chore_state.created_at,
                "updated_at": chore_state.updated_at,
            }

            # Update
            if request.next_executor_id is not None:
                chore_state.next_executor_id = request.next_executor_id
            if request.next_execution_date:
                chore_state.next_execution_date = request.next_execution_date
            chore_state.updated_at = utc_now_iso()

            # Capture after values
            after_values = {
                "id": chore_state.id,
                "chore_id": chore_state.chore_id,
                "last_executor_id": chore_state.last_executor_id,
                "last_execution_date": chore_state.last_execution_date,
                "next_executor_id": chore_state.next_executor_id,
                "next_execution_date": chore_state.next_execution_date,
                "created_at": chore_state.created_at,
                "updated_at": chore_state.updated_at,
            }

            # Log to audit
            audit_update(session, "chore_state", chore_state.id, before_values, after_values, "api")

            session.commit()
            return APIResponse(
                success=True,
                data=ChoreStateResponse(
                    id=chore_state.id,
                    chore_id=chore_state.chore_id,
                    last_executor_id=chore_state.last_executor_id,
                    last_execution_date=chore_state.last_execution_date,
                    next_executor_id=chore_state.next_executor_id,
                    next_execution_date=chore_state.next_execution_date,
                    created_at=chore_state.created_at,
                    updated_at=chore_state.updated_at,
                ),
            )
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    # ========================================================================
    # Ranking Endpoints
    # ========================================================================

    @router.post("/rankings", response_model=APIResponse)
    def create_or_update_ranking(request: RankingRequest):
        """Create or update a ranking."""
        session = db.get_session()
        try:
            # Validate person exists
            person = session.query(Person).filter(Person.id == request.person_id).first()
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")

            # Validate chore exists
            chore = session.query(Chore).filter(Chore.id == request.chore_id).first()
            if not chore:
                raise HTTPException(status_code=404, detail="Chore not found")

            # Check for existing ranking
            existing = session.query(Ranking).filter(
                (Ranking.person_id == request.person_id) & (Ranking.chore_id == request.chore_id)
            ).first()

            now = utc_now_iso()

            if existing:
                # Update
                before_values = {
                    "id": existing.id,
                    "person_id": existing.person_id,
                    "chore_id": existing.chore_id,
                    "rating": existing.rating,
                    "created_at": existing.created_at,
                    "updated_at": existing.updated_at,
                }

                existing.rating = request.rating
                existing.updated_at = now

                after_values = {
                    "id": existing.id,
                    "person_id": existing.person_id,
                    "chore_id": existing.chore_id,
                    "rating": existing.rating,
                    "created_at": existing.created_at,
                    "updated_at": existing.updated_at,
                }

                audit_update(session, "rankings", existing.id, before_values, after_values, "api")

                session.commit()
                return APIResponse(
                    success=True,
                    data=RankingResponse(
                        id=existing.id,
                        person_id=existing.person_id,
                        chore_id=existing.chore_id,
                        rating=existing.rating,
                        created_at=existing.created_at,
                        updated_at=existing.updated_at,
                    ),
                )
            else:
                # Create
                ranking = Ranking(
                    person_id=request.person_id,
                    chore_id=request.chore_id,
                    rating=request.rating,
                    created_at=now,
                    updated_at=now,
                )
                session.add(ranking)
                session.flush()

                audit_insert(
                    session,
                    "rankings",
                    ranking.id,
                    {
                        "id": ranking.id,
                        "person_id": ranking.person_id,
                        "chore_id": ranking.chore_id,
                        "rating": ranking.rating,
                        "created_at": ranking.created_at,
                        "updated_at": ranking.updated_at,
                    },
                    "api",
                )

                session.commit()
                return APIResponse(
                    success=True,
                    data=RankingResponse(
                        id=ranking.id,
                        person_id=ranking.person_id,
                        chore_id=ranking.chore_id,
                        rating=ranking.rating,
                        created_at=ranking.created_at,
                        updated_at=ranking.updated_at,
                    ),
                    
                )
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    @router.get("/rankings", response_model=APIResponse)
    def list_rankings(
        person_id: Optional[int] = None,
        chore_id: Optional[int] = None,
    ):
        """List rankings with optional filtering."""
        session = db.get_session()
        try:
            query = session.query(Ranking)

            if person_id:
                query = query.filter(Ranking.person_id == person_id)
            if chore_id:
                query = query.filter(Ranking.chore_id == chore_id)

            rankings = query.all()

            if len(rankings) > 1000:
                raise HTTPException(
                    status_code=400,
                    detail="Result set exceeds maximum limit of 1000 records. "
                    "Use filters to narrow your query.",
                )

            return APIResponse(
                success=True,
                data=[
                    RankingResponse(
                        id=r.id,
                        person_id=r.person_id,
                        chore_id=r.chore_id,
                        rating=r.rating,
                        created_at=r.created_at,
                        updated_at=r.updated_at,
                    )
                    for r in rankings
                ],
            )
        finally:
            session.close()

    @router.delete("/rankings/{person_id}/{chore_id}", status_code=204)
    def delete_ranking(person_id: int, chore_id: int):
        """Delete a ranking."""
        session = db.get_session()
        try:
            ranking = session.query(Ranking).filter(
                (Ranking.person_id == person_id) & (Ranking.chore_id == chore_id)
            ).first()
            if not ranking:
                raise HTTPException(status_code=404, detail="Ranking not found")

            before_values = {
                "id": ranking.id,
                "person_id": ranking.person_id,
                "chore_id": ranking.chore_id,
                "rating": ranking.rating,
                "created_at": ranking.created_at,
                "updated_at": ranking.updated_at,
            }

            audit_delete(session, "rankings", ranking.id, before_values, "api")

            session.delete(ranking)
            session.commit()
            return None
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            session.close()

    # ========================================================================
    # Composite Endpoints
    # ========================================================================

    @router.get("/summary", response_model=APIResponse)
    def get_chores_summary():
        """Get all chores with current state and rankings."""
        session = db.get_session()
        try:
            chores = (
                session.query(Chore)
                .options(
                    joinedload(Chore.state),
                    subqueryload(Chore.rankings),
                )
                .all()
            )

            if len(chores) > 1000:
                raise HTTPException(
                    status_code=400,
                    detail="Result set exceeds maximum limit of 1000 records. "
                    "Use filters to narrow your query.",
                )

            chores_data = []
            for chore in chores:
                state = chore.state

                chore_with_state = {
                    "id": chore.id,
                    "name": chore.name,
                    "frequency_in_weeks": chore.frequency_in_weeks,
                    "state": {
                        "id": state.id,
                        "chore_id": state.chore_id,
                        "last_executor_id": state.last_executor_id,
                        "last_execution_date": state.last_execution_date,
                        "next_executor_id": state.next_executor_id,
                        "next_execution_date": state.next_execution_date,
                        "created_at": state.created_at,
                        "updated_at": state.updated_at,
                    } if state else None,
                    "rankings": [
                        {"person_id": r.person_id, "rating": r.rating}
                        for r in chore.rankings
                    ],
                }
                chores_data.append(chore_with_state)

            return APIResponse(success=True, data={"chores": chores_data})
        finally:
            session.close()

    # ========================================================================
    # Audit Endpoints
    # ========================================================================

    @router.get("/audit", response_model=APIResponse)
    def query_audit(
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        operation: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ):
        """Query audit log with optional filtering."""
        session = db.get_session()
        try:
            entries = query_audit_log(
                session,
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                since=since,
                until=until,
            )

            return APIResponse(
                success=True,
                data=[
                    AuditLogEntryResponse(
                        id=e.id,
                        table_name=e.table_name,
                        operation=e.operation,
                        record_id=e.record_id,
                        before_values=e.before_values,
                        after_values=e.after_values,
                        changed_at=e.changed_at,
                        changed_by=e.changed_by,
                    )
                    for e in entries
                ],
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            session.close()

    return router
