# src/database.py
"""
Handles database interactions for logging pump operations.
Uses SQLite.
"""
import sqlite3
import datetime
from typing import List, Tuple, Optional
import logging

from config import DATABASE_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection() -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        logging.debug("Database connection established.")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise

def create_tables() -> None:
    """Creates the pump_logs table if it doesn't exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pump_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                pump_id TEXT NOT NULL,
                action TEXT NOT NULL CHECK(action IN ('START', 'STOP', 'ERROR', 'INFO', 'MANUAL_START', 'MANUAL_STOP')),
                reason TEXT,
                main_line_level_pct REAL,
                underground_level_pct REAL,
                overhead_level_pct REAL,
                active_meter TEXT,
                details TEXT
            )
        """)
        conn.commit()
        logging.info("Database table 'pump_logs' checked/created successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error creating database table: {e}")
    finally:
        if conn:
            conn.close()
            logging.debug("Database connection closed after table creation.")

def log_pump_action(
    pump_id: str,
    action: str,
    reason: str,
    levels: dict[str, float],
    active_meter: str,
    details: Optional[str] = None
) -> None:
    """Logs a pump action or system event to the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()
        cursor.execute("""
            INSERT INTO pump_logs (
                timestamp, pump_id, action, reason,
                main_line_level_pct, underground_level_pct, overhead_level_pct,
                active_meter, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, pump_id, action, reason,
            levels.get('main_line', None), levels.get('underground', None), levels.get('overhead', None),
            active_meter, details
        ))
        conn.commit()
        logging.info(f"Logged: Pump={pump_id}, Action={action}, Reason={reason}, Meter={active_meter}")
    except sqlite3.Error as e:
        logging.error(f"Error logging pump action: {e}")
    finally:
        if conn:
            conn.close()
            logging.debug("Database connection closed after logging.")

def get_recent_logs(limit: int = 50) -> List[sqlite3.Row]:
    """Retrieves the most recent log entries."""
    conn = get_db_connection()
    logs = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, pump_id, action, reason, main_line_level_pct, underground_level_pct, overhead_level_pct, active_meter, details
            FROM pump_logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        logs = cursor.fetchall()
        logging.debug(f"Retrieved {len(logs)} recent logs.")
    except sqlite3.Error as e:
        logging.error(f"Error retrieving logs: {e}")
    finally:
        if conn:
            conn.close()
            logging.debug("Database connection closed after retrieving logs.")
    return logs

# --- Initial Setup ---
# Create tables when the module is imported for the first time.
if __name__ != "__main__":
    create_tables()
