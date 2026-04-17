import logging
import sqlite3
import pickle
import datetime
from pathlib import Path
from typing import Any, Optional, TypeVar, Callable

# Database path in the app directory
DB_PATH = Path("/app/data_cache.db")

# Data type expiration times (in hours)
EXPIRATION_HOURS = {
    "zmanim": 24,
    "weather": 1,
    "calendar": 4,
    "chores": 4,
    "seating": 6,
}

T = TypeVar('T')

_logger: logging.Logger = None
"""This is the logger that the data_cache uses"""

def _humanize_age(now_utc: datetime.datetime, timestamp: datetime.datetime) -> str:
    """Return a compact human-readable age string."""
    delta_seconds = max(0, int((now_utc - timestamp).total_seconds()))

    if delta_seconds < 60:
        return "less than a minute"

    if delta_seconds < 3600:
        minutes = delta_seconds // 60
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit}"

    if delta_seconds < 86400:
        hours = delta_seconds // 3600
        unit = "hour" if hours == 1 else "hours"
        return f"{hours} {unit}"

    days = delta_seconds // 86400
    unit = "day" if days == 1 else "days"
    return f"{days} {unit}"


def init_db(logger: logging.Logger):
    """Initialize the SQLite database with the required schema."""
    global _logger
    _logger = logger

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type TEXT NOT NULL UNIQUE,
            data BLOB NOT NULL,
            timestamp DATETIME NOT NULL,
            expiration DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def clean_expired_records(older_than_days: int = 30):
    """Delete cached data records that have been expired for more than the specified days."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=older_than_days)

    cursor.execute(
        "DELETE FROM data_cache WHERE expiration < ?",
        (cutoff_date,)
    )

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted_count > 0:
        _logger.info(f"Deleted {deleted_count} expired cache records older than {older_than_days} days")


def get_cached_data(data_type: str, now_utc: datetime.datetime) -> Optional[tuple[Any,datetime.datetime]]:
    """
    Retrieve cached data if it hasn't expired.

    Args:
        data_type: The type of data (e.g., 'weather', 'zmanim')
        now_utc: The reference time to check expiration (should be UTC timezone-aware).

    Returns:
        tuple: (data, timestamp) if valid cached data exists, None otherwise.
                timestamp is always UTC timezone-aware.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT data, timestamp FROM data_cache WHERE data_type = ? AND expiration > ?",
        (data_type, now_utc)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        data_blob, timestamp_str = result
        data = pickle.loads(data_blob)
        # Parse ISO format and explicitly set UTC timezone if not already present
        timestamp = datetime.datetime.fromisoformat(timestamp_str)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)
        _logger.debug(f"get_cached_data(): fetched {data_type} data from cache with timestamp {timestamp.isoformat()}")
        return (data, timestamp)

    _logger.debug(f"get_cached_data(): no valid cached data for {data_type} (none, or may have already expired)")
    return None


def save_cached_data(data_type: str, data: T, now_utc: datetime.datetime) -> None:
    """
    Save data to cache with its expiration time.

    Args:
        data_type: The type of data (e.g., 'weather', 'zmanim')
        data: The data to cache
        now_utc: The reference time to calculate expiration (should be UTC timezone-aware).
    """
    if data_type not in EXPIRATION_HOURS:
        _logger.warning(f"Unknown data type: {data_type}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    expiration = now_utc + datetime.timedelta(hours=EXPIRATION_HOURS[data_type])

    data_blob = pickle.dumps(data)

    cursor.execute(
        """
        INSERT INTO data_cache (data_type, data, timestamp, expiration)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(data_type) DO UPDATE SET
            data = excluded.data,
            timestamp = excluded.timestamp,
            expiration = excluded.expiration
        """,
        (data_type, data_blob, now_utc.isoformat(), expiration.isoformat())
    )

    conn.commit()
    conn.close()

    _logger.info(f"Cached {data_type} data, expires at {expiration.isoformat()}")


def is_data_expired(data_type: str, now_utc: datetime.datetime) -> bool:
    """
    Check if cached data has expired or doesn't exist.

    Args:
        data_type: The type of data (e.g., 'weather', 'zmanim')
        now_utc: The reference time to check expiration (should be UTC timezone-aware)

    Returns:
        True if data is missing or expired, False if valid and fresh
    """
    if data_type not in EXPIRATION_HOURS:
        return True

    cached_result = get_cached_data(data_type, now_utc=now_utc)
    _logger.debug(f"is_data_expired(): data_type={data_type}, now_utc={now_utc.isoformat()}, cached_result={'found' if cached_result else 'not found or expired'}, cached_data_age={_humanize_age(now_utc=now_utc, timestamp=cached_result[1]) if cached_result else 'N/A'}")
    if cached_result is None:
        return True
    
    _, timestamp = cached_result
    if timestamp + datetime.timedelta(hours=EXPIRATION_HOURS[data_type]) <= now_utc:
        return True

    return False


def cache_or_fetch(data_type: str, fetch_fn: Callable[[], T], now_utc: datetime.datetime) -> T:
    """
    Get data from cache if valid, otherwise fetch using the provided function and cache it.

    Args:
        data_type: The type of data (e.g., 'weather', 'zmanim')
        fetch_fn: A callable that fetches the data if not cached
        now_utc: The reference time for cache expiration checks (should be UTC timezone-aware).

    Returns:
        The cached or freshly fetched data
    """

    # Check if we have valid cached data
    cached_result = get_cached_data(data_type, now_utc=now_utc)
    if cached_result:
        data, timestamp = cached_result
        age = _humanize_age(now_utc=now_utc, timestamp=timestamp)
        _logger.info(f"Using cached {data_type} data from {timestamp.isoformat()} ({age} old)")
        return data

    # Fetch new data
    _logger.info(f"Fetching fresh {data_type} data")
    data = fetch_fn()

    # Save to cache if data is not None
    if data is not None:
        save_cached_data(data_type, data, now_utc=now_utc)

    return data
