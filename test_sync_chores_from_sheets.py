#!/usr/bin/env python3
"""
Test suite for chores sync from Google Sheets.

Tests the complete sync pipeline:
1. Mock Google Sheets data
2. Clear existing chores
3. Insert fresh chores
4. Verify audit logging
"""

import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add workspace root to path
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from src.eink_backend.chores_db import ChoresDatabase, Chore, ChoreState, AuditLogEntry
from src.eink_backend.sync_chores_from_sheets import (
    get_chores_from_spreadsheet,
    clear_all_chores,
    insert_chores,
    sync_chores_from_sheets,
    parse_rankings_from_sheets,
    insert_rankings,
    get_people_from_database,
)
from src.eink_backend.migrate_chores_data import migrate_initial_people


def setup_test_database():
    """Create an in-memory test database."""
    db = ChoresDatabase("sqlite:///:memory:")
    db.init_db()
    # Initialize with people
    migrate_initial_people(db)
    return db


def test_mock_sheets_parsing():
    """Test that mock Google Sheets data parses correctly."""
    print("\n✓ Test: Mock Google Sheets parsing")
    
    mock_records = [
        {"Chore Name": "Clean Kitchen", "Frequency (weeks)": "1", "Ariel Difficulty Rating": "8", "Asaf Difficulty Rating": "6"},
        {"Chore Name": "Mop Floors", "Frequency (weeks)": "2", "Ariel Difficulty Rating": "7", "Asaf Difficulty Rating": "9"},
        {"Chore Name": "Bathroom", "Frequency (weeks)": "1"},
        {"Chore Name": "Take Out Trash", "Frequency (weeks)": "1", "Asaf Difficulty Rating": "5"},
    ]
    
    with patch('src.eink_backend.sync_chores_from_sheets.pygsheets') as mock_pygsheets:
        # Setup mock
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_records.return_value = mock_records
        
        mock_pygsheets.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_sheet
        mock_sheet.worksheet_by_title.return_value = mock_worksheet
        
        chores, records = get_chores_from_spreadsheet()
        
        assert len(chores) == 4, f"Expected 4 chores, got {len(chores)}"
        assert chores[0]["name"] == "Clean Kitchen"
        assert chores[0]["frequency_in_weeks"] == 1
        assert chores[1]["name"] == "Mop Floors"
        assert chores[1]["frequency_in_weeks"] == 2
        
        # Verify we got raw records for ranking parsing
        assert len(records) == 4
        
    print("  ✓ Mock sheets parsing verified")


def test_clear_all_chores():
    """Test clearing all existing chores."""
    print("\n✓ Test: Clear all existing chores")
    
    db = setup_test_database()
    session = db.get_session()
    
    # Insert some test chores
    from src.eink_backend.chores_db import utc_now_iso
    now = utc_now_iso()
    
    chore1 = Chore(name="Test Chore 1", frequency_in_weeks=1, created_at=now, updated_at=now)
    chore2 = Chore(name="Test Chore 2", frequency_in_weeks=2, created_at=now, updated_at=now)
    session.add(chore1)
    session.add(chore2)
    session.flush()
    
    chore_state1 = ChoreState(chore_id=chore1.id, created_at=now, updated_at=now)
    chore_state2 = ChoreState(chore_id=chore2.id, created_at=now, updated_at=now)
    session.add(chore_state1)
    session.add(chore_state2)
    session.commit()
    
    # Verify chores exist
    initial_count = session.query(Chore).count()
    assert initial_count == 2, f"Expected 2 chores, got {initial_count}"
    session.close()
    
    # Clear all chores
    deleted_count = clear_all_chores(db)
    
    # Verify all chores are deleted
    session = db.get_session()
    final_count = session.query(Chore).count()
    assert final_count == 0, f"Expected 0 chores after delete, got {final_count}"
    
    # Verify audit entries were created
    audit_count = session.query(AuditLogEntry).filter(
        AuditLogEntry.operation == "DELETE",
        AuditLogEntry.table_name == "chores"
    ).count()
    assert audit_count == 2, f"Expected 2 DELETE audit entries, got {audit_count}"
    
    session.close()
    db.close()
    
    print(f"  ✓ Deleted {deleted_count} chores with audit logging")


def test_insert_chores():
    """Test inserting chores into the database."""
    print("\n✓ Test: Insert chores into database")
    
    db = setup_test_database()
    
    chores_data = [
        {"name": "Clean Kitchen", "frequency_in_weeks": 1},
        {"name": "Mop Floors", "frequency_in_weeks": 2},
        {"name": "Bathroom", "frequency_in_weeks": 1},
    ]
    
    inserted_count, chores_by_name = insert_chores(db, chores_data)
    
    # Verify chores were inserted
    session = db.get_session()
    chore_count = session.query(Chore).count()
    assert chore_count == 3, f"Expected 3 chores, got {chore_count}"
    
    # Verify ChoreState records were created
    state_count = session.query(ChoreState).count()
    assert state_count == 3, f"Expected 3 chore states, got {state_count}"
    
    # Verify chores_by_name mapping
    assert len(chores_by_name) == 3
    assert chores_by_name["Clean Kitchen"] > 0
    assert chores_by_name["Mop Floors"] > 0
    
    # Verify audit entries
    insert_audit_count = session.query(AuditLogEntry).filter(
        AuditLogEntry.operation == "INSERT",
        AuditLogEntry.table_name == "chores"
    ).count()
    # Should have 3 INSERT entries for chores
    assert insert_audit_count >= 3, f"Expected at least 3 INSERT audit entries, got {insert_audit_count}"
    
    session.close()
    db.close()
    
    print(f"  ✓ Inserted {inserted_count} chores with mapping")


def test_rankings_parsing():
    """Test parsing difficulty ratings from Google Sheets."""
    print("\n✓ Test: Parse difficulty ratings from Sheets")
    
    db = setup_test_database()
    
    # Setup chores
    chores_data = [
        {"name": "Clean Kitchen", "frequency_in_weeks": 1},
        {"name": "Mop Floors", "frequency_in_weeks": 2},
    ]
    _, chores_by_name = insert_chores(db, chores_data)
    
    # Setup raw records with difficulty ratings
    raw_records = [
        {
            "Chore Name": "Clean Kitchen",
            "Frequency (weeks)": "1",
            "Ariel Difficulty Rating": "8",
            "Asaf Difficulty Rating": "6",
        },
        {
            "Chore Name": "Mop Floors",
            "Frequency (weeks)": "2",
            "Ariel Difficulty Rating": "7",
            "Asaf Difficulty Rating": "9",
        },
    ]
    
    people_by_name = get_people_from_database(db)
    assert len(people_by_name) > 0, "Should have people in database"
    
    rankings_data = parse_rankings_from_sheets(raw_records, chores_by_name, people_by_name)
    
    # Should have parsed at least some rankings
    assert len(rankings_data) > 0, f"Expected some rankings, got {len(rankings_data)}"
    
    # Check that ratings are in valid range
    for ranking in rankings_data:
        assert 1 <= ranking["rating"] <= 10, f"Rating out of range: {ranking['rating']}"
        assert ranking["person_id"] > 0
        assert ranking["chore_id"] > 0
    
    db.close()
    
    print(f"  ✓ Parsed {len(rankings_data)} difficulty ratings")


def test_full_sync():
    """Test the complete sync workflow."""
    print("\n✓ Test: Full sync workflow")
    
    db = setup_test_database()
    session = db.get_session()
    
    # Insert initial chores
    from src.eink_backend.chores_db import utc_now_iso
    now = utc_now_iso()
    
    initial_chore = Chore(name="Old Chore", frequency_in_weeks=1, created_at=now, updated_at=now)
    session.add(initial_chore)
    session.flush()
    
    initial_state = ChoreState(chore_id=initial_chore.id, created_at=now, updated_at=now)
    session.add(initial_state)
    session.commit()
    session.close()
    
    # Verify initial state
    session = db.get_session()
    assert session.query(Chore).count() == 1
    session.close()
    
    # Mock Google Sheets and perform sync
    mock_sheets_data = [
        {
            "Chore Name": "New Chore 1",
            "Frequency (weeks)": "1",
            "Ariel Difficulty Rating": "8",
        },
        {
            "Chore Name": "New Chore 2",
            "Frequency (weeks)": "2",
            "Asaf Difficulty Rating": "7",
        },
    ]
    
    with patch('src.eink_backend.sync_chores_from_sheets.pygsheets') as mock_pygsheets:
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_records.return_value = mock_sheets_data
        
        mock_pygsheets.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_sheet
        mock_sheet.worksheet_by_title.return_value = mock_worksheet
        
        sync_chores_from_sheets(db)
    
    # Verify final state
    session = db.get_session()
    
    # Old chore should be gone
    old_chore = session.query(Chore).filter(Chore.name == "Old Chore").first()
    assert old_chore is None, "Old chore should be deleted"
    
    # New chores should exist
    new_chore_count = session.query(Chore).count()
    assert new_chore_count == 2, f"Expected 2 new chores, got {new_chore_count}"
    
    # Verify new chores have correct data
    chore1 = session.query(Chore).filter(Chore.name == "New Chore 1").first()
    assert chore1 is not None
    assert chore1.frequency_in_weeks == 1
    
    chore2 = session.query(Chore).filter(Chore.name == "New Chore 2").first()
    assert chore2 is not None
    assert chore2.frequency_in_weeks == 2
    
    # Verify rankings were created
    from src.eink_backend.chores_db import Ranking
    ranking_count = session.query(Ranking).count()
    assert ranking_count > 0, "Should have created rankings from difficulty ratings"
    
    # Verify audit trail
    delete_audits = session.query(AuditLogEntry).filter(
        AuditLogEntry.operation == "DELETE",
        AuditLogEntry.table_name == "chores"
    ).count()
    assert delete_audits >= 1, "Should have DELETE audit entries for old chore"
    
    insert_audits = session.query(AuditLogEntry).filter(
        AuditLogEntry.operation == "INSERT",
        AuditLogEntry.table_name == "chores"
    ).count()
    assert insert_audits >= 2, "Should have INSERT audit entries for new chores"
    
    session.close()
    db.close()
    
    print("  ✓ Full sync workflow with rankings verified")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CHORES SYNC FROM GOOGLE SHEETS TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Mock Sheets Parsing", test_mock_sheets_parsing),
        ("Clear All Chores", test_clear_all_chores),
        ("Insert Chores", test_insert_chores),
        ("Parse Difficulty Ratings", test_rankings_parsing),
        ("Full Sync Workflow", test_full_sync),
    ]
    
    failed = []
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"  ✗ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed.append(test_name)
    
    print("\n" + "=" * 60)
    if not failed:
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print(f"✗ {len(failed)} TEST(S) FAILED:")
        for test_name in failed:
            print(f"  - {test_name}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
