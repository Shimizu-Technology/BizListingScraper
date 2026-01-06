"""Database connection management with Neon-compatible settings."""
import os
import time
import logging
from contextlib import contextmanager
import psycopg
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/bizlistings")

# Connection pool for better performance
pool = None

def init_pool(force_new: bool = False):
    """Initialize the connection pool."""
    global pool
    
    if force_new and pool is not None:
        try:
            pool.close()
        except Exception:
            pass
        pool = None
    
    if pool is None:
        pool = ConnectionPool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            timeout=30,
            max_idle=60,
            reconnect_timeout=5,
            kwargs={
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        )
    return pool

def get_pool():
    """Get or create the connection pool."""
    global pool
    if pool is None:
        init_pool()
    return pool

def reset_pool():
    """Reset the connection pool."""
    init_pool(force_new=True)
    logger.info("Connection pool reset")

@contextmanager
def get_connection(retries: int = 3):
    """Get a connection from the pool with retry logic."""
    last_error = None
    
    for attempt in range(retries):
        try:
            p = get_pool()
            conn = p.getconn()
            try:
                yield conn
            finally:
                # Always try to return connection to pool
                try:
                    p.putconn(conn)
                except Exception:
                    pass
            return
        except (psycopg.OperationalError, psycopg.InterfaceError) as e:
            last_error = e
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                try:
                    reset_pool()
                except Exception:
                    pass
                time.sleep(0.5)
    
    if last_error:
        raise last_error
    raise Exception("Failed to get database connection")

def close_pool():
    """Close the connection pool."""
    global pool
    if pool is not None:
        try:
            pool.close()
        except Exception:
            pass
        pool = None
