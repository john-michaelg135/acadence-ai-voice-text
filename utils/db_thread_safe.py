"""
Thread-safe database utilities for Acadence AI
Ensures all database operations are properly synchronized
"""
import sqlite3
import threading
from typing import Optional, Any, List, Tuple
from utils.logger import logger

class ThreadSafeDatabaseConnection:
    """
    Wrapper around sqlite3.Connection that ensures thread-safe access.
    All database operations must go through this wrapper.
    """
    
    def __init__(self, db_path: str):
        """Initialize a new thread-safe database connection."""
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.lock = threading.RLock()  # Reentrant lock allows same thread to acquire multiple times
        logger.debug(f"ThreadSafeDatabaseConnection initialized for {db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get or create the connection (thread-safe)."""
        with self.lock:
            if self.connection is None:
                self.connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=True,  # Re-enable thread checking
                    timeout=30.0  # Wait up to 30 seconds for locks
                )
                self.connection.row_factory = sqlite3.Row
                logger.debug(f"Database connection created for {self.db_path}")
            return self.connection
    
    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a query safely (thread-safe)."""
        with self.lock:
            try:
                cursor = self.get_connection().cursor()
                cursor.execute(query, params)
                self.get_connection().commit()
                return cursor
            except Exception as e:
                logger.error(f"Database execute failed: {e}", exc_info=True)
                self.get_connection().rollback()
                raise
    
    def executescript(self, script: str) -> sqlite3.Cursor:
        """Execute a script safely (thread-safe)."""
        with self.lock:
            try:
                cursor = self.get_connection().cursor()
                cursor.executescript(script)
                logger.debug("Database script executed successfully")
                return cursor
            except Exception as e:
                logger.error(f"Database executescript failed: {e}", exc_info=True)
                raise
    
    def fetchone(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row safely (thread-safe)."""
        with self.lock:
            try:
                cursor = self.get_connection().cursor()
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result
            except Exception as e:
                logger.error(f"Database fetchone failed: {e}", exc_info=True)
                raise
    
    def fetchall(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows safely (thread-safe)."""
        with self.lock:
            try:
                cursor = self.get_connection().cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                return results
            except Exception as e:
                logger.error(f"Database fetchall failed: {e}", exc_info=True)
                raise
    
    def transaction(self):
        """Context manager for transactions (thread-safe)."""
        return DatabaseTransaction(self.lock, self.get_connection())
    
    def close(self):
        """Close the connection safely."""
        with self.lock:
            if self.connection:
                try:
                    self.connection.close()
                    self.connection = None
                    logger.debug("Database connection closed")
                except Exception as e:
                    logger.error(f"Error closing database: {e}")


class DatabaseTransaction:
    """Context manager for database transactions."""
    
    def __init__(self, lock: threading.RLock, connection: sqlite3.Connection):
        self.lock = lock
        self.connection = connection
        self.cursor = None
    
    def __enter__(self):
        self.lock.acquire()
        try:
            self.cursor = self.connection.cursor()
            self.connection.execute("BEGIN")
            return self.cursor
        except Exception as e:
            self.lock.release()
            logger.error(f"Transaction begin failed: {e}", exc_info=True)
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
                logger.error(f"Transaction rolled back: {exc_val}")
        finally:
            self.lock.release()
