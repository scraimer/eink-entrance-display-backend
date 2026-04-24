"""
Sync chores data from Google Sheets to SQLite database.

This script performs a full refresh of chore data:
1. Fetches current chores and difficulty ratings from Google Sheets
2. Deletes all existing chores from the database (with cascade cleanup)
3. Repopulates with fresh chores from Sheets
4. Creates empty ChoreState records for each chore
5. Creates Ranking entries based on person-specific difficulty columns

All operations are logged to audit_log with changed_by='migration'
for full traceability and recovery capability.

Usage:
    from sync_chores_from_sheets import sync_chores_from_sheets
    sync_chores_from_sheets(db)
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
import pygsheets

from . import config
from .chores_db import ChoresDatabase, Chore, ChoreState, Person, Ranking, utc_now_iso
from .chores_audit import audit_insert, audit_delete


def get_chores_from_spreadsheet() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetch chores data and raw records from Google Sheets.
    
    Reads from the configured chores worksheet and returns:
    1. List of parsed chore records with 'name' and 'frequency_in_weeks'
    2. List of raw records for parsing difficulty ratings
    
    Expected columns: 'Chore Name', 'Frequency (weeks)', and optional
    '{PersonName} Difficulty Rating' columns for each person.
    
    Returns:
        Tuple of (parsed_chores, raw_records)
        
    Raises:
        Exception: If Google Sheets connection or parsing fails
    """
    gc: pygsheets.client.Client = pygsheets.authorize(
        service_file=config.config.google_sheets.json_file
    )
    sh: pygsheets.Spreadsheet = gc.open_by_key(config.config.google_sheets.sheet_id)
    worksheet: pygsheets.Worksheet = sh.worksheet_by_title(
        config.config.google_sheets.chores_worksheet_name
    )

    def parse_chore(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single chore record from the worksheet."""
        try:
            name = src.get("Name", "").strip()
            if not name:
                return None
            
            frequency_str = str(src.get("Frequency in Weeks", "1")).strip()
            try:
                frequency_in_weeks = int(frequency_str)
            except ValueError:
                print(f"Warning: Invalid frequency '{frequency_str}' for '{name}', defaulting to 1")
                frequency_in_weeks = 1
            
            # Ensure frequency is at least 1
            if frequency_in_weeks < 1:
                frequency_in_weeks = 1
            
            return {
                "name": name,
                "frequency_in_weeks": frequency_in_weeks,
            }
        except Exception as e:
            print(f"Error parsing chore record {src}: {e}")
            return None

    records = worksheet.get_all_records()
    chores: List[Dict[str, Any]] = []
    
    for record in records:
        chore = parse_chore(record)
        if chore:
            chores.append(chore)
    
    print(f"Fetched {len(chores)} chores from Google Sheets")
    return chores, records


def clear_all_chores(db: ChoresDatabase) -> int:
    """Delete all chores from the database.
    
    This cascades to delete all related:
    - ChoreState records
    - Execution records
    - Ranking records
    
    All deletions are logged to the audit log.
    
    Args:
        db: ChoresDatabase instance
        
    Returns:
        Number of chores deleted
    """
    session = db.get_session()
    try:
        # Query all existing chores
        existing_chores = session.query(Chore).all()
        count = 0
        
        for chore in existing_chores:
            # Serialize before_values for audit log
            before_values = {
                "id": chore.id,
                "name": chore.name,
                "frequency_in_weeks": chore.frequency_in_weeks,
                "created_at": chore.created_at,
                "updated_at": chore.updated_at,
            }
            
            # Create audit entry
            audit_delete(
                session,
                "chores",
                chore.id,
                before_values,
                changed_by="migration",
            )
            
            # Delete the chore (CASCADE will handle related records)
            session.delete(chore)
            count += 1
        
        session.commit()
        print(f"Deleted {count} chores from database")
        return count
        
    except Exception as e:
        session.rollback()
        print(f"Error while clearing chores: {e}")
        raise
    finally:
        session.close()


def get_people_from_database(db: ChoresDatabase) -> Dict[str, int]:
    """Fetch all people from the database.
    
    Returns a mapping of person names to their IDs.
    
    Args:
        db: ChoresDatabase instance
        
    Returns:
        Dictionary mapping person name -> person ID
    """
    session = db.get_session()
    try:
        people = session.query(Person).all()
        people_map = {person.name: person.id for person in people}
        session.close()
        return people_map
    except Exception as e:
        session.close()
        print(f"Warning: Could not fetch people from database: {e}")
        return {}


def parse_rankings_from_sheets(
    raw_records: List[Dict[str, Any]],
    chores_by_name: Dict[str, int],
    people_by_name: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Parse difficulty ratings from Google Sheets records.
    
    Looks for columns with format "{PersonName} Difficulty Rating" and creates
    ranking entries for each person-chore combination with a valid rating.
    
    Args:
        raw_records: Raw records from Google Sheets with all columns
        chores_by_name: Mapping of chore name -> chore ID
        people_by_name: Mapping of person name -> person ID
        
    Returns:
        List of dictionaries with 'person_id', 'chore_id', 'rating' keys
    """
    rankings: List[Dict[str, Any]] = []
    
    for record in raw_records:
        chore_name = record.get("Name", "").strip()
        if not chore_name or chore_name not in chores_by_name:
            continue
        
        chore_id = chores_by_name[chore_name]
        
        # Look for "{PersonName} Difficulty Rating" columns
        for person_name, person_id in people_by_name.items():
            rating_column = f"{person_name} Difficulty Rating"
            raw_rating = record.get(rating_column, "")
            rating_str = str(raw_rating).strip()
            
            if not rating_str:
                continue
            
            try:
                rating = int(rating_str)
                # Validate rating is between 1 and 10
                if 1 <= rating <= 10:
                    rankings.append({
                        "person_id": person_id,
                        "chore_id": chore_id,
                        "rating": rating,
                    })
                else:
                    print(f"Warning: Invalid rating {rating} for {person_name}/{chore_name}, skipping")
            except ValueError:
                print(f"Warning: Invalid rating value '{rating_str}' for {person_name}/{chore_name}, skipping")
    
    print(f"Parsed {len(rankings)} difficulty ratings from Google Sheets")
    return rankings


def insert_chores(db: ChoresDatabase, chores_data: List[Dict[str, Any]]) -> Tuple[int, Dict[str, int]]:
    """Insert chores into the database.
    
    Creates a Chore and associated ChoreState for each chore.
    All operations are logged to the audit log.
    
    Args:
        db: ChoresDatabase instance
        chores_data: List of chore dictionaries with 'name' and 'frequency_in_weeks'
        
    Returns:
        Tuple of (count, chores_by_name_map)
    """
    session = db.get_session()
    chores_by_name = {}
    try:
        now = utc_now_iso()
        count = 0
        
        for chore_dict in chores_data:
            # Create chore
            chore = Chore(
                name=chore_dict["name"],
                frequency_in_weeks=chore_dict["frequency_in_weeks"],
                created_at=now,
                updated_at=now,
            )
            session.add(chore)
            session.flush()
            
            # Store mapping for later ranking lookup
            chores_by_name[chore.name] = chore.id
            
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
            
            count += 1
            print(f"Inserted chore: {chore.name} (frequency: {chore.frequency_in_weeks} weeks)")
        
        session.commit()
        print(f"Inserted {count} chores into database")
        return count, chores_by_name
        
    except Exception as e:
        session.rollback()
        print(f"Error while inserting chores: {e}")
        raise
    finally:
        session.close()


def insert_rankings(db: ChoresDatabase, rankings_data: List[Dict[str, Any]]) -> int:
    """Insert rankings into the database.
    
    Creates Ranking entries for each person-chore difficulty rating.
    All operations are logged to the audit log.
    
    Args:
        db: ChoresDatabase instance
        rankings_data: List of ranking dictionaries with 'person_id', 'chore_id', 'rating'
        
    Returns:
        Number of rankings inserted
    """
    session = db.get_session()
    try:
        now = utc_now_iso()
        count = 0
        
        for ranking_dict in rankings_data:
            # Check if ranking already exists (shouldn't happen but be safe)
            existing = session.query(Ranking).filter(
                Ranking.person_id == ranking_dict["person_id"],
                Ranking.chore_id == ranking_dict["chore_id"],
            ).first()
            
            if existing:
                # Update existing ranking
                existing.rating = ranking_dict["rating"]
                existing.updated_at = now
                session.flush()
            else:
                # Create new ranking
                ranking = Ranking(
                    person_id=ranking_dict["person_id"],
                    chore_id=ranking_dict["chore_id"],
                    rating=ranking_dict["rating"],
                    created_at=now,
                    updated_at=now,
                )
                session.add(ranking)
                session.flush()
                
                # Audit log for insert
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
                    changed_by="migration",
                )
                count += 1
        
        session.commit()
        print(f"Inserted {count} difficulty ratings into database")
        return count
        
    except Exception as e:
        session.rollback()
        print(f"Error while inserting rankings: {e}")
        raise
    finally:
        session.close()


def sync_chores_from_sheets(db: ChoresDatabase) -> None:
    """Sync all chore data from Google Sheets to database.
    
    This performs a complete refresh:
    1. Fetches current chores from Google Sheets
    2. Deletes all existing chores from the database
    3. Inserts fresh chores from Sheets
    4. Creates empty ChoreState records
    5. Creates Ranking entries from difficulty ratings
    
    All operations are logged to audit_log with changed_by='migration'.
    
    Args:
        db: ChoresDatabase instance
        
    Raises:
        Exception: If any step fails (all-or-nothing operation)
    """
    print("\n=== Starting Chores Sync from Google Sheets ===")
    
    try:
        # Step 1: Fetch from Google Sheets
        print("\nStep 1: Fetching chores and difficulty ratings from Google Sheets...")
        chores_from_sheets, raw_records = get_chores_from_spreadsheet()
        
        if not chores_from_sheets:
            print("Warning: No chores found in Google Sheets")
            return
        
        # Step 2: Clear existing chores
        print("\nStep 2: Clearing existing chores from database...")
        deleted_count = clear_all_chores(db)
        
        # Step 3: Insert fresh chores
        print("\nStep 3: Inserting chores from Google Sheets...")
        inserted_count, chores_by_name = insert_chores(db, chores_from_sheets)
        
        # Step 4: Fetch people and parse rankings
        print("\nStep 4: Parsing difficulty ratings and creating rankings...")
        people_by_name = get_people_from_database(db)
        
        if people_by_name:
            rankings_data = parse_rankings_from_sheets(raw_records, chores_by_name, people_by_name)
            
            if rankings_data:
                # Step 5: Insert rankings
                print("\nStep 5: Inserting difficulty ratings into database...")
                inserted_rankings = insert_rankings(db, rankings_data)
            else:
                print("No difficulty ratings found in Google Sheets")
                inserted_rankings = 0
        else:
            print("Warning: No people found in database, skipping rankings")
            inserted_rankings = 0
        
        print("\n=== Chores Sync Complete ===")
        print(f"Summary: Deleted {deleted_count}, Inserted {inserted_count} chores, {inserted_rankings} ratings")
        
    except Exception as e:
        print(f"\nError during sync: {e}")
        raise
