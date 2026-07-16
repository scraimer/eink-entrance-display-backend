"""
FastAPI routes for chores management API.

Provides REST endpoints for:
- Chore management (CRUD)
                    "fixed_executor_id": state.fixed_executor_id,
- Execution tracking and scheduling
- Rankings management
- Audit log queries
- Summary data for rendering
"""

from typing import List, Optional, Dict, Any
import json
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
    DatedChorePlan,
    PersonData,
    ChoreData,
    ChoreStateData,
    ExecutionData,
    RankingData,
    AuditLogEntryData,
    compute_chore_scores,
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
    in_rotation: bool = True


class PersonResponse(BaseModel):
    """Response body for person data."""

    id: int
    name: str
    ordinal: int
    avatar: str
    in_rotation: bool
    created_at: str
    updated_at: str


class ChoreRequest(BaseModel):
    """Request body for creating/updating a chore."""

    name: str = Field(..., min_length=1, max_length=255)
    frequency_in_weeks: int = Field(..., ge=1)
    same_person_next_time: bool = False


class ChoreResponse(BaseModel):
    """Response body for chore data."""

    id: int
    name: str
    frequency_in_weeks: int
    same_person_next_time: bool
    created_at: str
    updated_at: str


class ChoreStateResponse(BaseModel):
    """Response body for chore state data."""

    id: int
    chore_id: int
    last_executor_id: Optional[int] = None
    last_execution_date: Optional[str] = None
    fixed_executor_id: Optional[int] = None
    next_execution_date: Optional[str] = None
    created_at: str
    updated_at: str


class ExecutionRequest(BaseModel):
    """Request body for performing an execution."""

    chore_id: int = Field(..., ge=1)
    executor_id: int = Field(..., ge=1)
    plan_date: Optional[str] = Field(
        None,
        description="Plan date to update after execution (YYYY-MM-DD, today, tomorrow).",
    )


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
    fixed_executor_id: Optional[int] = Field(None, ge=1)
    next_execution_date: Optional[str] = None

    @validator("next_execution_date")
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class BulkNextDueDateRequest(BaseModel):
    """Request body for bulk next due date updates."""

    chore_ids: List[int] = Field(..., min_items=1, max_items=10)
    next_execution_date: date

    @validator("chore_ids")
    def validate_chore_ids(cls, value: List[int]) -> List[int]:
        if any(chore_id < 1 for chore_id in value):
            raise ValueError("All chore IDs must be positive integers")
        if len(set(value)) != len(value):
            raise ValueError("chore_ids must not contain duplicates")
        return value


class BulkNextDueDateResponse(BaseModel):
    """Response body for bulk next due date updates."""

    chore_ids: List[int]
    next_execution_date: str
    updated_count: int


class PlanGenerationRequest(BaseModel):
    """Request body for generating a persisted chore plan."""

    plan_date: Optional[str] = Field(
        None,
        description="Target date in YYYY-MM-DD format, or shortcuts: today/tomorrow.",
    )


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


def _resolve_plan_date(plan_date: Optional[str]) -> str:
    if not plan_date or plan_date == "today":
        return date.today().isoformat()
    if plan_date == "tomorrow":
        return (date.today() + timedelta(days=1)).isoformat()
    try:
        return date.fromisoformat(plan_date).isoformat()
    except ValueError as ex:
        raise HTTPException(status_code=400, detail="plan_date must be YYYY-MM-DD, today, or tomorrow") from ex


def _build_plan_snapshot(
    session: Session,
    target_plan_date: str,
    done_chore_ids: Optional[set[int]] = None,
) -> dict[str, Any]:
    """Build a full chores plan snapshot for a specific date."""
    done_ids = done_chore_ids or set()
    scores_by_chore: dict[int, list[dict[str, Any]]] = {}
    for person_id, chore_id, score in compute_chore_scores(session, as_of_date_iso=target_plan_date):
        scores_by_chore.setdefault(chore_id, []).append({"person_id": person_id, "score": score})

    chores = (
        session.query(Chore)
        .options(
            joinedload(Chore.state),
            subqueryload(Chore.rankings),
        )
        .all()
    )

    chores_data: list[dict[str, Any]] = []
    for chore in chores:
        state = chore.state
        person_scores = scores_by_chore.get(chore.id, [])
        next_executor_id = (
            state.fixed_executor_id if chore.same_person_next_time and state else
            (person_scores[0]["person_id"] if person_scores else None)
        )
        chores_data.append({
            "id": chore.id,
            "name": chore.name,
            "frequency_in_weeks": chore.frequency_in_weeks,
            "same_person_next_time": chore.same_person_next_time,
            "plan_date": target_plan_date,
            "is_done": chore.id in done_ids,
            "state": {
                "id": state.id,
                "chore_id": state.chore_id,
                "last_executor_id": state.last_executor_id,
                "last_execution_date": state.last_execution_date,
                "fixed_executor_id": state.fixed_executor_id,
                "next_execution_date": state.next_execution_date,
                "created_at": state.created_at,
                "updated_at": state.updated_at,
            } if state else None,
            "next_executor_id": next_executor_id,
            "person_scores": person_scores if not chore.same_person_next_time else [],
            "rankings": (
                []
                if chore.same_person_next_time
                else [{"person_id": r.person_id, "rating": r.rating} for r in chore.rankings]
            ),
        })

    _rebalance_due_soon_assignments(chores_data, target_plan_date)

    return {
        "plan_date": target_plan_date,
        "done_chore_ids": sorted(done_ids),
        "chores": chores_data,
    }


def _rebalance_due_soon_assignments(
    chores_data: list[dict[str, Any]],
    target_plan_date: str,
) -> None:
    """Rebalance due-soon chore assignments so load gap is at most one."""
    try:
        plan_day = date.fromisoformat(target_plan_date)
    except ValueError:
        return
    tomorrow = plan_day + timedelta(days=1)

    rotation_ids = sorted({
        int(score["person_id"])
        for chore in chores_data
        for score in (chore.get("person_scores") or [])
    })
    if len(rotation_ids) < 2:
        return

    def is_due_soon(chore: dict[str, Any]) -> bool:
        due = (chore.get("state") or {}).get("next_execution_date")
        if not due:
            return False
        try:
            due_day = date.fromisoformat(due)
        except ValueError:
            return False
        return due_day in (plan_day, tomorrow)

    def count_assignments() -> dict[int, int]:
        counts = {person_id: 0 for person_id in rotation_ids}
        for chore in chores_data:
            if chore.get("is_done"):
                continue
            if not is_due_soon(chore):
                continue
            assignee = chore.get("next_executor_id")
            if assignee in counts:
                counts[int(assignee)] += 1
        return counts

    max_iterations = max(1, len(chores_data) * 4)
    for _ in range(max_iterations):
        counts = count_assignments()
        min_person = min(rotation_ids, key=lambda pid: (counts[pid], pid))
        max_person = max(rotation_ids, key=lambda pid: (counts[pid], pid))
        if counts[max_person] - counts[min_person] <= 1:
            return

        candidates: list[tuple[int, int, dict[str, Any]]] = []
        for chore in chores_data:
            if chore.get("is_done"):
                continue
            if chore.get("same_person_next_time"):
                continue
            if chore.get("next_executor_id") != max_person:
                continue
            if not is_due_soon(chore):
                continue

            person_scores = chore.get("person_scores") or []
            min_score_entry = next(
                (item for item in person_scores if int(item["person_id"]) == min_person),
                None,
            )
            if min_score_entry is None:
                continue
            candidates.append((int(min_score_entry["score"]), int(chore["id"]), chore))

        if not candidates:
            return

        candidates.sort(key=lambda item: (item[0], item[1]))
        _, _, chosen_chore = candidates[0]
        chosen_chore["next_executor_id"] = min_person


def generate_and_store_plan(
    db: ChoresDatabase,
    requested_plan_date: Optional[str] = None,
) -> dict[str, Any]:
    """Generate and persist a dated chore plan snapshot."""
    plan_date = _resolve_plan_date(requested_plan_date)
    session = db.get_session()
    try:
        row = session.query(DatedChorePlan).filter(DatedChorePlan.plan_date == plan_date).first()
        existing_done_ids: set[int] = set()
        if row is not None:
            try:
                existing_payload = json.loads(row.plan_data)
                existing_done_ids = {int(item) for item in existing_payload.get("done_chore_ids", [])}
            except (TypeError, ValueError):
                existing_done_ids = set()

        snapshot = _build_plan_snapshot(
            session,
            target_plan_date=plan_date,
            done_chore_ids=existing_done_ids,
        )
        now = utc_now_iso()
        if row is None:
            row = DatedChorePlan(
                plan_date=plan_date,
                plan_data=json.dumps(snapshot),
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            row.plan_data = json.dumps(snapshot)
            row.updated_at = now
        session.commit()
        return snapshot
    finally:
        session.close()


def _hide_chore_from_plan_snapshot(
    session: Session,
    plan_date: str,
    chore_id: int,
) -> None:
    """Mark a completed chore as done in the persisted plan snapshot for a specific date."""
    plan_row = session.query(DatedChorePlan).filter(DatedChorePlan.plan_date == plan_date).first()
    if plan_row is None:
        snapshot = _build_plan_snapshot(session, target_plan_date=plan_date, done_chore_ids={chore_id})
        plan_row = DatedChorePlan(
            plan_date=plan_date,
            plan_data=json.dumps(snapshot),
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(plan_row)
        session.flush()

    payload = json.loads(plan_row.plan_data)
    done_ids = {int(item) for item in payload.get("done_chore_ids", [])}
    done_ids.add(chore_id)
    payload["done_chore_ids"] = sorted(done_ids)
    chores = payload.get("chores", [])
    for item in chores:
        item_id = int(item.get("id", -1))
        item["is_done"] = item_id in done_ids
    plan_row.plan_data = json.dumps(payload)
    plan_row.updated_at = utc_now_iso()


def seed_default_chore_plans(db: ChoresDatabase) -> None:
    """Ensure startup has persisted plan snapshots for today and tomorrow."""
    generate_and_store_plan(db, "today")
    generate_and_store_plan(db, "tomorrow")


def refresh_tomorrow_chore_plan(db: ChoresDatabase) -> None:
    """Refresh the tomorrow plan snapshot (scheduler target)."""
    generate_and_store_plan(db, "tomorrow")


def build_chores_summary(
    db: ChoresDatabase,
    plan_date: Optional[str] = None,
) -> dict[str, list[dict[str, Any]]]:
    """Get all chores with current state and rankings for a persisted plan date.

    Args:
        db: ChoresDatabase instance to query

    Returns:
        Dict with a "chores" key containing a list of chore dicts with state and rankings.
    """
    effective_plan_date = _resolve_plan_date(plan_date)
    session = db.get_session()
    try:
        persisted = session.query(DatedChorePlan).filter(
            DatedChorePlan.plan_date == effective_plan_date
        ).first()
        if persisted:
            payload = json.loads(persisted.plan_data)
            done_ids = {int(item) for item in payload.get("done_chore_ids", [])}
            chores = payload.get("chores", [])
            for chore in chores:
                chore.setdefault("plan_date", effective_plan_date)
                chore_id = int(chore.get("id", -1))
                chore["is_done"] = chore_id in done_ids or bool(chore.get("is_done", False))
            return {"chores": chores}
    finally:
        session.close()

    generated = generate_and_store_plan(db, effective_plan_date)
    chores = generated.get("chores", [])
    for chore in chores:
        chore.setdefault("plan_date", effective_plan_date)
    return {"chores": chores}


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
                in_rotation=request.in_rotation,
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
                    "in_rotation": person.in_rotation,
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
                    in_rotation=person.in_rotation,
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
                    in_rotation=person.in_rotation,
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
                        in_rotation=p.in_rotation,
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
                "in_rotation": person.in_rotation,
                "created_at": person.created_at,
                "updated_at": person.updated_at,
            }

            # Update
            person.name = request.name
            person.ordinal = request.ordinal
            person.avatar = request.avatar
            person.in_rotation = request.in_rotation
            person.updated_at = utc_now_iso()

            # Capture after values
            after_values = {
                "id": person.id,
                "name": person.name,
                "ordinal": person.ordinal,
                "avatar": person.avatar,
                "in_rotation": person.in_rotation,
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
                    in_rotation=person.in_rotation,
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
                "in_rotation": person.in_rotation,
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
                (ChoreState.fixed_executor_id == person_id)
            ).all()
            for state in chore_states:
                before_state = {
                    "id": state.id,
                    "chore_id": state.chore_id,
                    "last_executor_id": state.last_executor_id,
                    "last_execution_date": state.last_execution_date,
                    "fixed_executor_id": state.fixed_executor_id,
                    "next_execution_date": state.next_execution_date,
                    "created_at": state.created_at,
                    "updated_at": state.updated_at,
                }
                
                # Update the state
                if state.last_executor_id == person_id:
                    state.last_executor_id = None
                if state.fixed_executor_id == person_id:
                    state.fixed_executor_id = None
                state.updated_at = utc_now_iso()
                
                after_state = {
                    "id": state.id,
                    "chore_id": state.chore_id,
                    "last_executor_id": state.last_executor_id,
                    "last_execution_date": state.last_execution_date,
                    "fixed_executor_id": state.fixed_executor_id,
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
                same_person_next_time=request.same_person_next_time,
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
                    "same_person_next_time": chore.same_person_next_time,
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
                    "fixed_executor_id": None,
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
                    same_person_next_time=chore.same_person_next_time,
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
                    same_person_next_time=chore.same_person_next_time,
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
                        same_person_next_time=c.same_person_next_time,
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
                "same_person_next_time": chore.same_person_next_time,
                "created_at": chore.created_at,
                "updated_at": chore.updated_at,
            }

            # Update
            chore.name = request.name
            chore.frequency_in_weeks = request.frequency_in_weeks
            chore.same_person_next_time = request.same_person_next_time
            chore.updated_at = utc_now_iso()

            # Capture after values
            after_values = {
                "id": chore.id,
                "name": chore.name,
                "frequency_in_weeks": chore.frequency_in_weeks,
                "same_person_next_time": chore.same_person_next_time,
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
                    same_person_next_time=chore.same_person_next_time,
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
                "fixed_executor_id": chore_state.fixed_executor_id,
                "next_execution_date": chore_state.next_execution_date,
                "created_at": chore_state.created_at,
                "updated_at": chore_state.updated_at,
            }

            # Update state
            chore_state.last_executor_id = request.executor_id
            chore_state.last_execution_date = today
            if chore.same_person_next_time:
                chore_state.fixed_executor_id = request.executor_id
            chore_state.next_execution_date = next_execution_date
            chore_state.updated_at = now

            # Capture after values
            after_state = {
                "id": chore_state.id,
                "chore_id": chore_state.chore_id,
                "last_executor_id": chore_state.last_executor_id,
                "last_execution_date": chore_state.last_execution_date,
                "fixed_executor_id": chore_state.fixed_executor_id,
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

            effective_plan_date = _resolve_plan_date(request.plan_date)
            _hide_chore_from_plan_snapshot(
                session=session,
                plan_date=effective_plan_date,
                chore_id=request.chore_id,
            )

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
                        fixed_executor_id=chore_state.fixed_executor_id,
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
        """Modify fixed executor and/or next execution date for a chore."""
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
            if request.fixed_executor_id:
                person = session.query(Person).filter(
                    Person.id == request.fixed_executor_id
                ).first()
                if not person:
                    raise HTTPException(status_code=404, detail="Person not found")

            # Capture before values
            before_values = {
                "id": chore_state.id,
                "chore_id": chore_state.chore_id,
                "last_executor_id": chore_state.last_executor_id,
                "last_execution_date": chore_state.last_execution_date,
                "fixed_executor_id": chore_state.fixed_executor_id,
                "next_execution_date": chore_state.next_execution_date,
                "created_at": chore_state.created_at,
                "updated_at": chore_state.updated_at,
            }

            # Update
            if request.fixed_executor_id is not None:
                chore_state.fixed_executor_id = request.fixed_executor_id
            if request.next_execution_date:
                chore_state.next_execution_date = request.next_execution_date
            chore_state.updated_at = utc_now_iso()

            # Capture after values
            after_values = {
                "id": chore_state.id,
                "chore_id": chore_state.chore_id,
                "last_executor_id": chore_state.last_executor_id,
                "last_execution_date": chore_state.last_execution_date,
                "fixed_executor_id": chore_state.fixed_executor_id,
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
                    fixed_executor_id=chore_state.fixed_executor_id,
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

    @router.put("/executions/bulk-next-due-date", response_model=APIResponse)
    def bulk_update_next_due_date(request: BulkNextDueDateRequest):
        """Update next due date for multiple chores in one all-or-nothing request."""
        session = db.get_session()
        try:
            chore_ids = request.chore_ids
            due_date = request.next_execution_date.isoformat()

            existing_chores = session.query(Chore).filter(Chore.id.in_(chore_ids)).all()
            existing_ids = {chore.id for chore in existing_chores}
            missing_chore_ids = [chore_id for chore_id in chore_ids if chore_id not in existing_ids]
            if missing_chore_ids:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chore(s) not found: {', '.join(str(chore_id) for chore_id in missing_chore_ids)}",
                )

            states = session.query(ChoreState).filter(ChoreState.chore_id.in_(chore_ids)).all()
            states_by_chore_id = {state.chore_id: state for state in states}
            missing_state_ids = [chore_id for chore_id in chore_ids if chore_id not in states_by_chore_id]
            if missing_state_ids:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Chore state not found for chore(s): "
                        f"{', '.join(str(chore_id) for chore_id in missing_state_ids)}"
                    ),
                )

            now = utc_now_iso()
            for chore_id in chore_ids:
                state = states_by_chore_id[chore_id]
                before_values = {
                    "id": state.id,
                    "chore_id": state.chore_id,
                    "last_executor_id": state.last_executor_id,
                    "last_execution_date": state.last_execution_date,
                    "fixed_executor_id": state.fixed_executor_id,
                    "next_execution_date": state.next_execution_date,
                    "created_at": state.created_at,
                    "updated_at": state.updated_at,
                }

                state.next_execution_date = due_date
                state.updated_at = now

                after_values = {
                    "id": state.id,
                    "chore_id": state.chore_id,
                    "last_executor_id": state.last_executor_id,
                    "last_execution_date": state.last_execution_date,
                    "fixed_executor_id": state.fixed_executor_id,
                    "next_execution_date": state.next_execution_date,
                    "created_at": state.created_at,
                    "updated_at": state.updated_at,
                }
                audit_update(session, "chore_state", state.id, before_values, after_values, "api")

            session.commit()
            return APIResponse(
                success=True,
                data=BulkNextDueDateResponse(
                    chore_ids=chore_ids,
                    next_execution_date=due_date,
                    updated_count=len(chore_ids),
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

    @router.post("/plans/generate", response_model=APIResponse)
    def generate_plan(request: PlanGenerationRequest):
        """Generate or refresh a persisted chores plan for a selected date."""
        plan = generate_and_store_plan(db, request.plan_date)
        return APIResponse(success=True, data=plan)

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
        """List rankings with optional filtering. Excludes chores flagged same_person_next_time."""
        session = db.get_session()
        try:
            query = session.query(Ranking).join(Chore, Ranking.chore_id == Chore.id).filter(
                Chore.same_person_next_time == False  # noqa: E712
            )

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
    def get_chores_summary(plan_date: Optional[str] = Query(None)):
        chores_data = build_chores_summary(db, plan_date=plan_date)
        return APIResponse(success=True, data=chores_data)

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
