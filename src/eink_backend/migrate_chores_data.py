"""
Data migration script for chores from Google Sheets to SQLite database.

This script performs a one-time migration of:
1. Initial people data (extracted from current chores.py)
2. Chores and frequencies from Google Sheets

Migration records all operations to audit_log with changed_by='migration'
for full traceability and recovery capability.

Usage:
    from migrate_chores_data import migrate_initial_people, migrate_chores_from_sheets
    migrate_initial_people(db)
    migrate_chores_from_sheets(db)
"""

from sqlalchemy.orm import Session
from datetime import datetime

from .chores_db import ChoresDatabase, Person, Chore, ChoreState, utc_now_iso, utc_today_iso
from .chores_audit import audit_insert


def migrate_initial_people(db: ChoresDatabase) -> None:
    """Migrate initial people from hardcoded TABLE in chores.py.
    
    This creates the core set of people who perform chores:
    - Ariel (ordinal 1, avatar ariel.png)
    - Asaf (ordinal 2, avatar asaf.png)
    - Amalya (ordinal 3, avatar amalya.png)
    - Alon (ordinal 4, avatar alon.png)
    - Aviv (ordinal 5, avatar aviv.png)
    
    Args:
        db: ChoresDatabase instance
    """
    session = db.get_session()
    try:
        # Data extracted from chores.py normalize_assigneed TABLE
        initial_people = [
            {"name": "Ariel", "ordinal": 1, "avatar": "ariel.png"},
            {"name": "Asaf", "ordinal": 2, "avatar": "asaf.png"},
            {"name": "Amalya", "ordinal": 3, "avatar": "amalya.png"},
            {"name": "Alon", "ordinal": 4, "avatar": "alon.png"},
            {"name": "Aviv", "ordinal": 5, "avatar": "aviv.png"},
        ]

        now = utc_now_iso()
        
        for person_data in initial_people:
            # Check if person already exists
            existing = session.query(Person).filter(
                Person.name == person_data["name"]
            ).first()
            
            if existing:
                print(f"Skipping {person_data['name']} - already exists")
                continue
            
            # Create person
            person = Person(
                name=person_data["name"],
                ordinal=person_data["ordinal"],
                avatar=person_data["avatar"],
                created_at=now,
                updated_at=now,
            )
            session.add(person)
            session.flush()
            
            # Audit log
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
                changed_by="migration",
            )
            
            print(f"Created person: {person.name} (ordinal {person.ordinal})")
        
        session.commit()
        print("Migration of initial people completed successfully")
        
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        session.close()


def migrate_chores_from_sheets(db: ChoresDatabase, chores_data: list) -> None:
    """Migrate chores data from Google Sheets.
    
    Expected format of chores_data:
    [
        {"name": "Chore Name", "frequency_in_weeks": 1},
        ...
    ]
    
    Args:
        db: ChoresDatabase instance
        chores_data: List of chore dictionaries with 'name' and 'frequency_in_weeks'
    """
    session = db.get_session()
    try:
        now = utc_now_iso()
        
        for chore_dict in chores_data:
            # Check if chore already exists
            existing = session.query(Chore).filter(
                Chore.name == chore_dict["name"]
            ).first()
            
            if existing:
                print(f"Skipping {chore_dict['name']} - already exists")
                continue
            
            # Create chore
            chore = Chore(
                name=chore_dict["name"],
                frequency_in_weeks=chore_dict["frequency_in_weeks"],
                created_at=now,
                updated_at=now,
            )
            session.add(chore)
            session.flush()
            
            # Create empty chore_state
            chore_state = ChoreState(
                chore_id=chore.id,
                created_at=now,
                updated_at=now,
            )
            session.add(chore_state)
            session.flush()
            
            # Audit log for chore
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
                changed_by="migration",
            )
            
            # Audit log for chore_state
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
                changed_by="migration",
            )
            
            print(f"Created chore: {chore.name} (every {chore.frequency_in_weeks} weeks)")
        
        session.commit()
        print("Migration of chores completed successfully")
        
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        session.close()
