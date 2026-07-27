#!/usr/bin/env python3
"""Tests for persisted dated chore plans."""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta, timezone

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from eink_backend import chores as chores_module
from eink_backend import main as main_module
import eink_backend.chores_api as chores_api
from eink_backend.chores_db import ChoresDatabase, DatedChorePlan, Person
from eink_backend.chores_api import (
    _rebalance_due_soon_assignments,
    build_chores_summary,
    create_chores_router,
    generate_and_store_plan,
    refresh_tomorrow_chore_plan,
)


def setup_db(name: str):
    db_path = Path(__file__).parent / f"test_dated_plan_{name}.sqlite"
    if db_path.exists():
        db_path.unlink()
    db = ChoresDatabase(f"sqlite:///{db_path}")
    db.init_db()
    db.migrate_db()
    return db, db_path


def make_client(db: ChoresDatabase) -> TestClient:
    app = FastAPI()
    app.include_router(create_chores_router(db))
    return TestClient(app)


def seed_people_and_chore(client: TestClient):
    for payload in [
        {"name": "Alice", "ordinal": 1, "avatar": "alice.png"},
        {"name": "Bob", "ordinal": 2, "avatar": "bob.png"},
    ]:
        r = client.post("/api/v1/chores/people", json=payload)
        assert r.status_code == 201, r.text

    chore = client.post(
        "/api/v1/chores/chores",
        json={"name": "Dishes", "frequency_in_weeks": 1, "same_person_next_time": False},
    )
    assert chore.status_code == 201, chore.text
    return chore.json()["data"]["id"]


def test_today_tomorrow_and_iso_plan_generation():
    db, db_path = setup_db("today_tomorrow")
    client = make_client(db)
    seed_people_and_chore(client)

    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    arbitrary = "2026-07-20"

    assert client.post("/api/v1/chores/plans/generate", json={"plan_date": "today"}).status_code == 200
    assert client.post("/api/v1/chores/plans/generate", json={"plan_date": "tomorrow"}).status_code == 200
    assert client.post("/api/v1/chores/plans/generate", json={"plan_date": arbitrary}).status_code == 200

    for expected in [today, tomorrow, arbitrary]:
        summary = client.get(f"/api/v1/chores/summary?plan_date={expected}")
        assert summary.status_code == 200, summary.text
        chores = summary.json()["data"]["chores"]
        assert chores, "Expected at least one chore in summary"
        assert all(chore["plan_date"] == expected for chore in chores)

    session = db.get_session()
    try:
        plan_dates = {row.plan_date for row in session.query(DatedChorePlan).all()}
        assert today in plan_dates
        assert tomorrow in plan_dates
        assert arbitrary in plan_dates
    finally:
        session.close()
        db.close()
        db_path.unlink()


def test_execution_hides_chore_from_selected_plan():
    db, db_path = setup_db("execution_no_refresh")
    client = make_client(db)
    chore_id = seed_people_and_chore(client)

    target = "2026-07-21"
    first = client.post("/api/v1/chores/plans/generate", json={"plan_date": target})
    assert first.status_code == 200, first.text
    before = first.json()["data"]
    assert len(before["chores"]) == 1

    people = client.get("/api/v1/chores/people").json()["data"]
    alice = next(p for p in people if p["name"] == "Alice")
    done = client.post(
        "/api/v1/chores/executions",
        json={"chore_id": chore_id, "executor_id": alice["id"], "plan_date": target},
    )
    assert done.status_code == 201, done.text

    after = client.get(f"/api/v1/chores/summary?plan_date={target}")
    assert after.status_code == 200, after.text
    chores = after.json()["data"]["chores"]
    assert len(chores) == 1
    assert chores[0]["id"] == chore_id
    assert chores[0]["is_done"] is True

    db.close()
    db_path.unlink()


def test_midnight_helper_matches_manual_generation_format():
    db, db_path = setup_db("midnight_helper")
    client = make_client(db)
    seed_people_and_chore(client)

    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    manual = generate_and_store_plan(db, tomorrow)
    refresh_tomorrow_chore_plan(db)
    refreshed = client.get(f"/api/v1/chores/summary?plan_date={tomorrow}")
    assert refreshed.status_code == 200, refreshed.text
    refreshed_payload = {"plan_date": tomorrow, "chores": refreshed.json()["data"]["chores"]}

    assert refreshed_payload["plan_date"] == manual["plan_date"]
    assert len(refreshed_payload["chores"]) == len(manual["chores"])
    if refreshed_payload["chores"]:
        assert set(refreshed_payload["chores"][0].keys()) == set(manual["chores"][0].keys())

    db.close()
    db_path.unlink()


def test_summary_without_plan_date_defaults_to_today_plan():
    db, db_path = setup_db("default_summary_today")
    client = make_client(db)
    seed_people_and_chore(client)

    today = date.today().isoformat()
    assert client.post("/api/v1/chores/plans/generate", json={"plan_date": "today"}).status_code == 200

    default_summary = client.get("/api/v1/chores/summary")
    assert default_summary.status_code == 200, default_summary.text
    chores = default_summary.json()["data"]["chores"]
    assert chores, "Expected chores in default summary"
    assert all(chore["plan_date"] == today for chore in chores)

    db.close()
    db_path.unlink()


def test_chores_collect_data_uses_today_plan():
    db, db_path = setup_db("collect_data_today")
    client = make_client(db)
    seed_people_and_chore(client)

    assert client.post("/api/v1/chores/plans/generate", json={"plan_date": "today"}).status_code == 200

    main_module.chores_db = db
    try:
        result = chores_module.collect_data(now_utc=datetime.now(timezone.utc))
        assert result.error is None
        assert result.chores, "Expected chores from today plan"
    finally:
        main_module.chores_db = None

    db.close()
    db_path.unlink()


def test_build_chores_summary_today_matches_today_plan():
    db, db_path = setup_db("build_summary_today")
    client = make_client(db)
    seed_people_and_chore(client)

    today = date.today().isoformat()
    assert client.post("/api/v1/chores/plans/generate", json={"plan_date": "today"}).status_code == 200

    today_summary = client.get(f"/api/v1/chores/summary?plan_date={today}")
    assert today_summary.status_code == 200, today_summary.text
    today_chores = today_summary.json()["data"]["chores"]
    assert today_chores, "Expected chores in today plan summary"

    direct_summary = build_chores_summary(db, plan_date="today")
    direct_chores = direct_summary["chores"]
    assert direct_chores, "Expected chores from direct build_chores_summary"
    assert len(direct_chores) == len(today_chores)
    assert {chore["id"] for chore in direct_chores} == {chore["id"] for chore in today_chores}
    assert all(chore["plan_date"] == today for chore in direct_chores)

    db.close()
    db_path.unlink()


def test_chores_from_summary_uses_next_executor_if_same_person_flag_is_false():
    db, db_path = setup_db("fixed_executor_ignore")
    main_module.chores_db = db
    now = datetime.now(timezone.utc).isoformat()
    session = db.get_session()
    try:
        session.add(Person(name="Ariel", ordinal=1, avatar="ariel.png", created_at=now, updated_at=now))
        session.add(Person(name="Alon", ordinal=4, avatar="alon.png", created_at=now, updated_at=now))
        session.commit()
        alon_id = session.query(Person).filter(Person.name == "Alon").one().id
        ariel_id = session.query(Person).filter(Person.name == "Ariel").one().id
    finally:
        session.close()

    try:
        summary = {
            "chores": [
                {
                    "id": 1,
                    "name": "Playroom",
                    "frequency_in_weeks": 1,
                    "same_person_next_time": False,
                    "plan_date": "2026-07-31",
                    "is_done": False,
                    "state": {
                        "next_execution_date": "2026-07-31",
                        "fixed_executor_id": ariel_id,
                    },
                    "next_executor_id": alon_id,
                    "person_scores": [],
                }
            ]
        }
        chores = chores_module._chores_from_summary(summary)
        assert len(chores) == 1
        assert chores[0].assignee == "Alon"
    finally:
        main_module.chores_db = None
        db.close()
        db_path.unlink()


def test_rebalance_keeps_due_soon_gap_within_one():
    plan_date = "2026-07-20"
    chores = []
    for chore_id in range(1, 9):
        chores.append({
            "id": chore_id,
            "name": f"Chore {chore_id}",
            "same_person_next_time": False,
            "is_done": False,
            "state": {"next_execution_date": "2026-07-20"},
            "next_executor_id": 1,
            "person_scores": [
                {"person_id": 1, "score": 10},
                {"person_id": 2, "score": 20 + chore_id},
                {"person_id": 3, "score": 30 + chore_id},
                {"person_id": 4, "score": 40 + chore_id},
            ],
        })

    _rebalance_due_soon_assignments(chores, plan_date)

    counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for chore in chores:
        counts[chore["next_executor_id"]] += 1
    assert max(counts.values()) - min(counts.values()) <= 1


def test_rebalance_moves_chores_when_one_person_has_five_or_more_due_soon_chores():
    plan_date = "2026-07-20"
    chores = []
    for chore_id in range(1, 6):
        chores.append({
            "id": chore_id,
            "name": f"Chore {chore_id}",
            "same_person_next_time": False,
            "is_done": False,
            "state": {"next_execution_date": "2026-07-20"},
            "next_executor_id": 1,
            "person_scores": [
                {"person_id": 1, "score": 10},
                {"person_id": 2, "score": 20 + chore_id},
                {"person_id": 3, "score": 30 + chore_id},
            ],
        })

    _rebalance_due_soon_assignments(chores, plan_date)

    counts = {1: 0, 2: 0, 3: 0}
    for chore in chores:
        counts[chore["next_executor_id"]] += 1

    assert counts[1] < 5, "Expected overloaded person 1 to shed chores when assigned 5 or more due-soon items"
    assert counts[2] > 0 or counts[3] > 0, "Expected at least one chore to be reassigned to another person"
    assert max(counts.values()) - min(counts.values()) <= 1


def main():
    tests = [
        test_today_tomorrow_and_iso_plan_generation,
        test_execution_hides_chore_from_selected_plan,
        test_midnight_helper_matches_manual_generation_format,
        test_summary_without_plan_date_defaults_to_today_plan,
        test_chores_collect_data_uses_today_plan,
        test_rebalance_keeps_due_soon_gap_within_one,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except Exception as ex:
            failed += 1
            print(f"FAIL: {test.__name__}: {ex}")
    if failed:
        sys.exit(1)
    print("All dated chore plan tests passed")


if __name__ == "__main__":
    main()
