#!/usr/bin/env python3
"""
Test ON DELETE CASCADE for person deletion.

This test verifies that deleting a person properly cascades to:
- Delete all executions where they are the executor
- Delete all rankings where they are the rater
- Set chore_state.last_executor_id to NULL if they were the last executor
- Set chore_state.next_executor_id to NULL if they were the next executor
- Create appropriate audit log entries for all changes

Usage:
    python test_person_cascade_delete.py
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from datetime import datetime, date
from eink_backend.chores_db import ChoresDatabase, Person, Chore, ChoreState, Execution, Ranking
from eink_backend.migrate_chores_data import migrate_initial_people
from eink_backend.chores_api import create_chores_router
from eink_backend.chores_audit import query_audit_log
from fastapi import FastAPI
from fastapi.testclient import TestClient


def setup_test_db():
    """Create and initialize test database."""
    db_path = Path(__file__).parent / "test_person_cascade.sqlite"
    if db_path.exists():
        db_path.unlink()
    
    database_url = f"sqlite:///{db_path}"
    db = ChoresDatabase(database_url)
    db.init_db()
    
    # Seed initial people
    migrate_initial_people(db)
    
    return db, db_path


def main():
    """Run person deletion cascade test."""
    print("\nPerson Deletion Cascade Test")
    print("=" * 60)
    
    try:
        # Setup
        db, db_path = setup_test_db()
        
        # Create test client
        app = FastAPI()
        router = create_chores_router(db)
        app.include_router(router)
        client = TestClient(app)
        
        # Get people for testing
        session = db.get_session()
        people = session.query(Person).order_by(Person.ordinal).all()
        person_to_delete = people[0]  # Ariel
        other_person = people[1]      # Asaf
        session.close()
        
        print(f"\nTesting deletion of person: {person_to_delete.name} (ID {person_to_delete.id})")
        
        # Create a chore
        print("\n1. Creating test chore...")
        response = client.post("/api/v1/chores/chores", json={
            "name": "PersonCascadeTestChore",
            "frequency_in_weeks": 1
        })
        assert response.status_code == 201
        chore_id = response.json()["data"]["id"]
        print(f"   ✓ Created chore {chore_id}")
        
        # Create an execution with the person to be deleted
        print(f"\n2. Creating execution with {person_to_delete.name}...")
        response = client.post("/api/v1/chores/executions", json={
            "chore_id": chore_id,
            "executor_id": person_to_delete.id
        })
        assert response.status_code == 201
        state = response.json()["data"]["updated_state"]
        execution_id = response.json()["data"]["execution"]["id"]
        print(f"   ✓ Created execution {execution_id}")
        print(f"   ✓ Last executor: {state['last_executor_id']} ({person_to_delete.name})")
        print(f"   ✓ Next executor: {state['next_executor_id']}")
        
        # Create a ranking with the person to be deleted
        print(f"\n3. Creating ranking with {person_to_delete.name}...")
        response = client.post("/api/v1/chores/rankings", json={
            "person_id": person_to_delete.id,
            "chore_id": chore_id,
            "rating": 8
        })
        assert response.status_code == 200
        ranking_id = response.json()["data"]["id"]
        print(f"   ✓ Created ranking {ranking_id}")
        
        # Create another ranking with the other person
        print(f"\n4. Creating ranking with {other_person.name}...")
        response = client.post("/api/v1/chores/rankings", json={
            "person_id": other_person.id,
            "chore_id": chore_id,
            "rating": 6
        })
        assert response.status_code == 200
        print(f"   ✓ Created ranking for {other_person.name}")
        
        # Delete the person
        print(f"\n5. Deleting {person_to_delete.name}...")
        response = client.delete(f"/api/v1/chores/people/{person_to_delete.id}")
        assert response.status_code == 204
        print(f"   ✓ Person deleted")
        
        # Verify cascade deletions
        print("\n6. Verifying cascade deletions...")
        session = db.get_session()
        
        # Check execution was deleted
        execution_count = session.query(Execution).filter(
            Execution.executor_id == person_to_delete.id
        ).count()
        assert execution_count == 0, f"Executions not deleted ({execution_count} found)"
        print(f"   ✓ Executions cascade deleted")
        
        # Check ranking was deleted
        ranking_count = session.query(Ranking).filter(
            Ranking.person_id == person_to_delete.id
        ).count()
        assert ranking_count == 0, f"Ranking not deleted ({ranking_count} found)"
        print(f"   ✓ Rankings cascade deleted")
        
        # Check other person's ranking still exists
        other_ranking_count = session.query(Ranking).filter(
            Ranking.person_id == other_person.id,
            Ranking.chore_id == chore_id
        ).count()
        assert other_ranking_count == 1, f"Other ranking deleted ({other_ranking_count} found)"
        print(f"   ✓ Other person's ranking preserved")
        
        # Check chore_state was updated
        chore_state = session.query(ChoreState).filter(
            ChoreState.chore_id == chore_id
        ).first()
        assert chore_state is not None, "ChoreState was deleted"
        assert chore_state.last_executor_id is None, "last_executor_id not set to NULL"
        assert chore_state.next_executor_id is not None, "next_executor_id was set to NULL (should not be)"
        print(f"   ✓ ChoreState.last_executor_id set to NULL")
        print(f"   ✓ ChoreState.next_executor_id preserved: {chore_state.next_executor_id}")
        
        # Verify audit log entries
        print("\n7. Verifying audit log entries...")
        
        # Check for person deletion
        delete_entries = query_audit_log(
            session,
            table_name="people",
            operation="DELETE"
        )
        assert len(delete_entries) >= 1, "No person DELETE entry found"
        found_delete = False
        for entry in delete_entries:
            if entry.record_id == person_to_delete.id:
                found_delete = True
                assert entry.changed_by == "api", f"Delete has changed_by='{entry.changed_by}'"
                break
        assert found_delete, f"Person {person_to_delete.id} not found in DELETE entries"
        print(f"   ✓ Person DELETE audit entry created")
        
        # Check for chore_state updates
        state_entries = query_audit_log(
            session,
            table_name="chore_state",
            record_id=chore_state.id,
            operation="UPDATE"
        )
        assert len(state_entries) > 0, "No chore_state UPDATE entry found"
        print(f"   ✓ ChoreState UPDATE audit entries created")
        
        # Check for execution deletion
        exec_entries = query_audit_log(
            session,
            table_name="executions",
            operation="DELETE"
        )
        assert len(exec_entries) >= 1, "No execution DELETE entry found"
        print(f"   ✓ Execution DELETE audit entries created")
        
        # Check for ranking deletion
        rank_entries = query_audit_log(
            session,
            table_name="rankings",
            operation="DELETE"
        )
        assert len(rank_entries) >= 1, "No ranking DELETE entry found"
        print(f"   ✓ Ranking DELETE audit entries created")
        
        session.close()
        
        # Cleanup
        db.close()
        if db_path.exists():
            db_path.unlink()
        
        print("\n" + "="*60)
        print("✓ PERSON CASCADE DELETE TEST PASSED")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
