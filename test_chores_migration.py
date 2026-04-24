#!/usr/bin/env python3
"""
Test script to verify chores database initialization and migration.

This script:
1. Initializes the chores database
2. Seeds initial people data
3. Verifies the data was inserted correctly
4. Tests basic API connectivity

Usage:
    python test_chores_migration.py
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from eink_backend.chores_db import ChoresDatabase, Person
from eink_backend.migrate_chores_data import migrate_initial_people


def test_database_initialization():
    """Test that database initializes correctly."""
    print("\n" + "="*60)
    print("TEST 1: Database Initialization")
    print("="*60)
    
    db_path = Path(__file__).parent / "test_chores.sqlite"
    
    # Clean up any existing test database
    if db_path.exists():
        db_path.unlink()
        print(f"✓ Cleaned up old test database: {db_path}")
    
    # Initialize database with proper SQLite URL format
    database_url = f"sqlite:///{db_path}"
    db = ChoresDatabase(database_url)
    db.init_db()
    print(f"✓ Database initialized at: {db_path}")
    
    # Verify tables exist
    session = db.get_session()
    try:
        count = session.query(Person).count()
        print(f"✓ People table exists (current count: {count})")
    finally:
        session.close()
    
    return db, db_path


def test_people_migration(db):
    """Test that people migration works correctly."""
    print("\n" + "="*60)
    print("TEST 2: Initial People Migration")
    print("="*60)
    
    # Run migration
    migrate_initial_people(db)
    
    # Verify data
    session = db.get_session()
    try:
        people = session.query(Person).order_by(Person.ordinal).all()
        
        expected_people = [
            ("Ariel", 1, "ariel.png"),
            ("Asaf", 2, "asaf.png"),
            ("Amalya", 3, "amalya.png"),
            ("Alon", 4, "alon.png"),
            ("Aviv", 5, "aviv.png"),
        ]
        
        if len(people) != len(expected_people):
            print(f"✗ Expected {len(expected_people)} people, got {len(people)}")
            return False
        
        print(f"✓ Found {len(people)} people")
        
        for person, (expected_name, expected_ordinal, expected_avatar) in zip(people, expected_people):
            if (person.name != expected_name or 
                person.ordinal != expected_ordinal or 
                person.avatar != expected_avatar):
                print(f"✗ Person mismatch: {person.name} (ordinal {person.ordinal}, avatar {person.avatar})")
                return False
            
            print(f"  ✓ {person.name} (ID {person.id}, ordinal {person.ordinal}, avatar {person.avatar})")
        
        return True
    finally:
        session.close()


def test_audit_logging(db):
    """Test that audit logging captured the migration."""
    print("\n" + "="*60)
    print("TEST 3: Audit Logging Verification")
    print("="*60)
    
    from eink_backend.chores_audit import query_audit_log
    
    session = db.get_session()
    try:
        # Query audit entries for people table
        entries = query_audit_log(
            session,
            table_name="people",
            operation="INSERT"
        )
        
        if not entries:
            print("✗ No audit entries found for people INSERT operations")
            return False
        
        print(f"✓ Found {len(entries)} audit entries for people INSERT")
        
        for entry in entries:
            if entry.changed_by != "migration":
                print(f"✗ Entry {entry.id} has changed_by='{entry.changed_by}', expected 'migration'")
                return False
            
            print(f"  ✓ Entry {entry.id}: changed_by='migration'")
        
        return True
    finally:
        session.close()


def test_api_response_structure(db):
    """Test that API response structure is correct."""
    print("\n" + "="*60)
    print("TEST 4: API Response Structure")
    print("="*60)
    
    from eink_backend.chores_api import create_chores_router
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    
    # Create a minimal FastAPI app with our router
    app = FastAPI()
    router = create_chores_router(db)
    app.include_router(router)
    
    client = TestClient(app)
    
    # Test GET /people
    response = client.get("/api/v1/chores/people")
    
    if response.status_code != 200:
        print(f"✗ GET /people returned {response.status_code}")
        return False
    
    data = response.json()
    
    if not isinstance(data, dict):
        print(f"✗ Response is not a dict: {type(data)}")
        return False
    
    if "success" not in data or "data" not in data:
        print(f"✗ Response missing 'success' or 'data' keys")
        return False
    
    if not data["success"]:
        print(f"✗ Response success=false: {data.get('error')}")
        return False
    
    people_list = data.get("data", [])
    if not isinstance(people_list, list):
        print(f"✗ Response data is not a list: {type(people_list)}")
        return False
    
    if len(people_list) != 5:
        print(f"✗ Expected 5 people in response, got {len(people_list)}")
        return False
    
    print(f"✓ GET /people returned 200 with valid structure")
    print(f"✓ Response contains {len(people_list)} people in correct format")
    
    # Test GET /summary
    response = client.get("/api/v1/chores/summary")
    
    if response.status_code != 200:
        print(f"✗ GET /summary returned {response.status_code}")
        return False
    
    data = response.json()
    
    if not data.get("success"):
        print(f"✗ /summary response success=false: {data.get('error')}")
        return False
    
    if "chores" not in data.get("data", {}):
        print(f"✗ /summary response missing 'chores' key")
        return False
    
    print(f"✓ GET /summary returned 200 with valid structure")
    
    return True


def cleanup(db, db_path):
    """Clean up test database."""
    print("\n" + "="*60)
    print("Cleanup")
    print("="*60)
    
    db.close()
    if db_path.exists():
        db_path.unlink()
        print(f"✓ Cleaned up test database: {db_path}")


def main():
    """Run all tests."""
    print("\nChores Database Migration Tests")
    print("=" * 60)
    
    try:
        # Test 1: Database initialization
        db, db_path = test_database_initialization()
        
        # Test 2: People migration
        if not test_people_migration(db):
            print("\n✗ People migration test FAILED")
            cleanup(db, db_path)
            return 1
        
        # Test 3: Audit logging
        if not test_audit_logging(db):
            print("\n✗ Audit logging test FAILED")
            cleanup(db, db_path)
            return 1
        
        # Test 4: API response structure
        if not test_api_response_structure(db):
            print("\n✗ API response structure test FAILED")
            cleanup(db, db_path)
            return 1
        
        # Cleanup
        cleanup(db, db_path)
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return 0
        
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
