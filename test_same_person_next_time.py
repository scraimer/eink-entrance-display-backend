#!/usr/bin/env python3
"""
Tests for the same_person_next_time feature on chores.

Covers:
- Executor is NOT rotated when chore has same_person_next_time=True
- Executor IS rotated normally when same_person_next_time=False
- Rankings endpoint excludes chores with same_person_next_time=True
- GET /chores includes same_person_next_time field in responses

Usage:
    python test_same_person_next_time.py
"""

import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from eink_backend.chores_db import ChoresDatabase, Person, Chore, ChoreState, Ranking
from eink_backend.chores_api import create_chores_router
from eink_backend.chores_audit import query_audit_log
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def setup_test_db(name: str):
    db_path = Path(__file__).parent / f"test_spnt_{name}.sqlite"
    if db_path.exists():
        db_path.unlink()
    db = ChoresDatabase(f"sqlite:///{db_path}")
    db.init_db()
    return db, db_path


def make_client(db: ChoresDatabase) -> TestClient:
    app = FastAPI()
    router = create_chores_router(db)
    app.include_router(router)
    return TestClient(app)


def seed_people(client: TestClient):
    """Add two people: Alice (ordinal=1) and Bob (ordinal=2)."""
    for person in [
        {"name": "Alice", "ordinal": 1, "avatar": "alice.png"},
        {"name": "Bob", "ordinal": 2, "avatar": "bob.png"},
    ]:
        r = client.post("/api/v1/chores/people", json=person)
        assert r.status_code == 201, f"Seeding person failed: {r.text}"
    people = client.get("/api/v1/chores/people").json()["data"]
    return {p["name"]: p["id"] for p in people}


def create_chore(client: TestClient, name: str, freq: int = 1, same_person: bool = False) -> dict:
    r = client.post("/api/v1/chores/chores", json={
        "name": name,
        "frequency_in_weeks": freq,
        "same_person_next_time": same_person,
    })
    assert r.status_code == 201, f"Creating chore failed: {r.text}"
    return r.json()["data"]


def schedule_chore(client: TestClient, chore_id: int, next_executor_id: int):
    r = client.put("/api/v1/chores/executions/next-executor", json={
        "chore_id": chore_id,
        "next_executor_id": next_executor_id,
        "next_execution_date": "2026-05-01",
    })
    assert r.status_code == 200, f"Scheduling failed: {r.text}"


def mark_done(client: TestClient, chore_id: int, executor_id: int) -> dict:
    r = client.post("/api/v1/chores/executions", json={
        "chore_id": chore_id,
        "executor_id": executor_id,
    })
    assert r.status_code == 201, f"Mark done failed: {r.text}"
    return r.json()["data"]


# ---------------------------------------------------------------------------
# Test 7.1 – same_person_next_time=True keeps next_executor_id unchanged
# ---------------------------------------------------------------------------

def test_same_person_executor_not_rotated():
    print("\n" + "="*60)
    print("TEST 7.1: same_person_next_time=True — executor not rotated")
    print("="*60)

    db, db_path = setup_test_db("7_1")
    client = make_client(db)
    people = seed_people(client)

    alice_id = people["Alice"]
    bob_id = people["Bob"]

    # Create a flagged chore, scheduled for Alice
    chore = create_chore(client, "Cook dinner", same_person=True)
    assert chore["same_person_next_time"] is True, "Flag not persisted"
    schedule_chore(client, chore["id"], alice_id)

    # Mark as done by Alice
    result = mark_done(client, chore["id"], alice_id)
    next_executor_id = result["updated_state"]["next_executor_id"]

    assert next_executor_id == alice_id, (
        f"Expected next_executor_id to stay Alice ({alice_id}), got {next_executor_id}"
    )
    print(f"  ✓ next_executor_id stayed Alice ({alice_id}) — not rotated to Bob ({bob_id})")

    db.close()
    db_path.unlink()


# ---------------------------------------------------------------------------
# Test 7.2 – same_person_next_time=False advances next_executor_id normally
# ---------------------------------------------------------------------------

def test_normal_chore_executor_is_rotated():
    print("\n" + "="*60)
    print("TEST 7.2: same_person_next_time=False — executor is rotated")
    print("="*60)

    db, db_path = setup_test_db("7_2")
    client = make_client(db)
    people = seed_people(client)

    alice_id = people["Alice"]
    bob_id = people["Bob"]

    # Create a normal chore, scheduled for Alice
    chore = create_chore(client, "Wash dishes", same_person=False)
    assert chore["same_person_next_time"] is False
    schedule_chore(client, chore["id"], alice_id)

    # Mark as done by Alice — should rotate to Bob
    result = mark_done(client, chore["id"], alice_id)
    next_executor_id = result["updated_state"]["next_executor_id"]

    assert next_executor_id == bob_id, (
        f"Expected next_executor_id to advance to Bob ({bob_id}), got {next_executor_id}"
    )
    print(f"  ✓ next_executor_id advanced from Alice ({alice_id}) to Bob ({bob_id})")

    db.close()
    db_path.unlink()


# ---------------------------------------------------------------------------
# Test 7.3 – Rankings endpoint excludes same_person_next_time chores
# ---------------------------------------------------------------------------

def test_rankings_excludes_flagged_chores():
    print("\n" + "="*60)
    print("TEST 7.3: Rankings endpoint excludes flagged chores")
    print("="*60)

    db, db_path = setup_test_db("7_3")
    client = make_client(db)
    people = seed_people(client)

    alice_id = people["Alice"]

    # Create one normal and one flagged chore
    normal_chore = create_chore(client, "Mop floors", same_person=False)
    flagged_chore = create_chore(client, "Cook special meal", same_person=True)

    # Add a ranking for both chores for Alice
    for chore_id in [normal_chore["id"], flagged_chore["id"]]:
        r = client.post("/api/v1/chores/rankings", json={
            "person_id": alice_id,
            "chore_id": chore_id,
            "rating": 5,
        })
        assert r.status_code == 200, f"Ranking creation failed: {r.text}"

    # Fetch rankings
    r = client.get("/api/v1/chores/rankings")
    assert r.status_code == 200
    rankings = r.json()["data"]

    chore_ids_in_rankings = {rank["chore_id"] for rank in rankings}

    assert normal_chore["id"] in chore_ids_in_rankings, "Normal chore should appear in rankings"
    assert flagged_chore["id"] not in chore_ids_in_rankings, (
        f"Flagged chore (id={flagged_chore['id']}) should NOT appear in rankings"
    )
    print(f"  ✓ Flagged chore (id={flagged_chore['id']}) absent from rankings response")
    print(f"  ✓ Normal chore (id={normal_chore['id']}) present in rankings response")

    db.close()
    db_path.unlink()


# ---------------------------------------------------------------------------
# Test 7.4 – GET /chores includes same_person_next_time field
# ---------------------------------------------------------------------------

def test_chores_list_includes_flag():
    print("\n" + "="*60)
    print("TEST 7.4: GET /chores includes same_person_next_time field")
    print("="*60)

    db, db_path = setup_test_db("7_4")
    client = make_client(db)

    # Create chores with and without flag
    normal = create_chore(client, "Sweep", same_person=False)
    flagged = create_chore(client, "Special task", same_person=True)

    r = client.get("/api/v1/chores/chores")
    assert r.status_code == 200
    chores = r.json()["data"]

    by_id = {c["id"]: c for c in chores}

    assert "same_person_next_time" in by_id[normal["id"]], "Field missing from normal chore response"
    assert "same_person_next_time" in by_id[flagged["id"]], "Field missing from flagged chore response"
    assert by_id[normal["id"]]["same_person_next_time"] is False
    assert by_id[flagged["id"]]["same_person_next_time"] is True

    print("  ✓ same_person_next_time=False present in normal chore response")
    print("  ✓ same_person_next_time=True present in flagged chore response")

    db.close()
    db_path.unlink()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    passed = 0
    failed = 0
    tests = [
        test_same_person_executor_not_rotated,
        test_normal_chore_executor_is_rotated,
        test_rankings_excludes_flagged_chores,
        test_chores_list_includes_flag,
    ]
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
