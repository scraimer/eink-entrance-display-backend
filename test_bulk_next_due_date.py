#!/usr/bin/env python3
"""Tests for bulk next due date update API and chores UI wiring."""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from eink_backend.chores_api import create_chores_router
from eink_backend.chores_db import ChoreState, ChoresDatabase
from eink_backend.chores_ui import generate_chores_ui_html


def setup_test_db(name: str) -> tuple[ChoresDatabase, Path]:
    db_path = Path(__file__).parent / f"test_bulk_next_due_date_{name}.sqlite"
    if db_path.exists():
        db_path.unlink()
    db = ChoresDatabase(f"sqlite:///{db_path}")
    db.init_db()
    return db, db_path


def make_client(db: ChoresDatabase) -> TestClient:
    app = FastAPI()
    app.include_router(create_chores_router(db))
    return TestClient(app)


def create_chore(client: TestClient, name: str) -> int:
    response = client.post(
        "/api/v1/chores/chores",
        json={"name": name, "frequency_in_weeks": 1, "same_person_next_time": False},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


def get_state(session, chore_id: int) -> ChoreState:
    state = session.query(ChoreState).filter(ChoreState.chore_id == chore_id).first()
    assert state is not None
    return state


def test_bulk_next_due_date_success_updates_all_requested_chores():
    db, db_path = setup_test_db("success")
    client = make_client(db)
    try:
        chore_a = create_chore(client, "Vacuum")
        chore_b = create_chore(client, "Mop")

        response = client.put(
            "/api/v1/chores/executions/bulk-next-due-date",
            json={"chore_ids": [chore_a, chore_b], "next_execution_date": "2026-06-15"},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["updated_count"] == 2
        assert payload["data"]["next_execution_date"] == "2026-06-15"

        session = db.get_session()
        try:
            assert get_state(session, chore_a).next_execution_date == "2026-06-15"
            assert get_state(session, chore_b).next_execution_date == "2026-06-15"
        finally:
            session.close()
    finally:
        db.close()
        if db_path.exists():
            db_path.unlink()


def test_bulk_next_due_date_rejects_empty_selection():
    db, db_path = setup_test_db("empty")
    client = make_client(db)
    try:
        response = client.put(
            "/api/v1/chores/executions/bulk-next-due-date",
            json={"chore_ids": [], "next_execution_date": "2026-06-15"},
        )
        assert response.status_code == 422
    finally:
        db.close()
        if db_path.exists():
            db_path.unlink()


def test_bulk_next_due_date_rejects_non_date_only_value():
    db, db_path = setup_test_db("invalid_date")
    client = make_client(db)
    try:
        chore_id = create_chore(client, "Laundry")
        response = client.put(
            "/api/v1/chores/executions/bulk-next-due-date",
            json={"chore_ids": [chore_id], "next_execution_date": "2026-06-15T09:00:00Z"},
        )
        assert response.status_code == 422
    finally:
        db.close()
        if db_path.exists():
            db_path.unlink()


def test_bulk_next_due_date_rejects_above_limit():
    db, db_path = setup_test_db("limit")
    client = make_client(db)
    try:
        chore_ids = [create_chore(client, f"Chore {i}") for i in range(11)]
        response = client.put(
            "/api/v1/chores/executions/bulk-next-due-date",
            json={"chore_ids": chore_ids, "next_execution_date": "2026-06-15"},
        )
        assert response.status_code == 422
    finally:
        db.close()
        if db_path.exists():
            db_path.unlink()


def test_bulk_next_due_date_is_all_or_nothing_on_failure():
    db, db_path = setup_test_db("transaction")
    client = make_client(db)
    try:
        chore_id = create_chore(client, "Dishes")

        # Seed an existing date so we can verify rollback behavior.
        schedule_response = client.put(
            "/api/v1/chores/executions/next-executor",
            json={
                "chore_id": chore_id,
                "fixed_executor_id": None,
                "next_execution_date": "2026-06-01",
            },
        )
        assert schedule_response.status_code == 200, schedule_response.text

        response = client.put(
            "/api/v1/chores/executions/bulk-next-due-date",
            json={"chore_ids": [chore_id, 999999], "next_execution_date": "2026-06-20"},
        )
        assert response.status_code == 404

        session = db.get_session()
        try:
            assert get_state(session, chore_id).next_execution_date == "2026-06-01"
        finally:
            session.close()
    finally:
        db.close()
        if db_path.exists():
            db_path.unlink()


def test_chores_ui_contains_bulk_due_date_controls():
    html = generate_chores_ui_html()
    assert "bulk-next-date" in html
    assert "bulk-apply-btn" in html
    assert "/executions/bulk-next-due-date" in html
