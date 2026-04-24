#!/usr/bin/env python3
"""
Standalone database tools script for syncing chores from Google Sheets to database.

This script can be run independently to sync chore data without starting the full
FastAPI application. Useful for initialization, testing, and manual updates.

Usage:
    python -m src.eink_backend.chores_db_tools sync-sheets
    python -m src.eink_backend.chores_db_tools clear-chores
    python -m src.eink_backend.chores_db_tools init-db
    python -m src.eink_backend.chores_db_tools people-init
"""

import argparse
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the root directory (2 levels up from this file)
root_dir = Path(__file__).parent.parent.parent


def setup_database():
    """Initialize and return a ChoresDatabase instance."""
    from .chores_db import ChoresDatabase
    
    database_path = root_dir / "chores.sqlite"
    database_url = f"sqlite:///{database_path}"
    logger.info(f"Using database: {database_url}")
    
    db = ChoresDatabase(database_url)
    db.init_db()
    logger.info("Database initialized")
    return db


def sync_from_sheets():
    """Sync all chores from Google Sheets to database."""
    logger.info("Starting chores sync from Google Sheets...")
    
    try:
        db = setup_database()
        from .sync_chores_from_sheets import sync_chores_from_sheets
        
        sync_chores_from_sheets(db)
        db.close()
        logger.info("✓ Sync completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Sync failed: {e}", exc_info=True)
        return 1


def clear_chores():
    """Clear all chores from the database (cascading deletes)."""
    logger.warning("Clearing all chores from database...")
    
    try:
        db = setup_database()
        from .sync_chores_from_sheets import clear_all_chores
        
        deleted_count = clear_all_chores(db)
        db.close()
        logger.info(f"✓ Deleted {deleted_count} chores")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Clear failed: {e}", exc_info=True)
        return 1


def init_people():
    """Initialize the database with default people."""
    logger.info("Initializing people...")
    
    try:
        db = setup_database()
        from .migrate_chores_data import migrate_initial_people
        
        migrate_initial_people(db)
        db.close()
        logger.info("✓ People initialized successfully")
        return 0
        
    except Exception as e:
        logger.error(f"✗ People initialization failed: {e}", exc_info=True)
        return 1


def full_init():
    """Full initialization: create tables and initialize people."""
    logger.info("Performing full database initialization...")
    
    try:
        db = setup_database()
        from .migrate_chores_data import migrate_initial_people
        
        migrate_initial_people(db)
        db.close()
        logger.info("✓ Full initialization completed")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Full initialization failed: {e}", exc_info=True)
        return 1


def main():
    """Parse arguments and execute the appropriate command."""
    parser = argparse.ArgumentParser(
        description="Manage chores database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.eink_backend.chores_db_tools sync-sheets  # Sync from Google Sheets
  python -m src.eink_backend.chores_db_tools clear-chores # Clear all chores
  python -m src.eink_backend.chores_db_tools init-db      # Initialize database
  python -m src.eink_backend.chores_db_tools people-init  # Initialize people only
        """,
    )
    
    parser.add_argument(
        "command",
        choices=["sync-sheets", "clear-chores", "init-db", "people-init"],
        help="Command to execute",
    )
    
    args = parser.parse_args()
    
    commands = {
        "sync-sheets": sync_from_sheets,
        "clear-chores": clear_chores,
        "init-db": full_init,
        "people-init": init_people,
    }
    
    try:
        return commands[args.command]()
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
