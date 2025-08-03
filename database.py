"""
Database configuration and management for Candlestick Screener.
Handles PostgreSQL connections with connection pooling optimized for serverless deployments.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager with connection pooling for serverless compatibility"""
    
    def __init__(self):
        self.connection_pool: Optional[pool.ThreadedConnectionPool] = None
        self._initialize_pool()
    
    def _get_database_url(self) -> str:
        """Get the appropriate database URL based on environment"""
        env = os.getenv('FLASK_ENV', 'development')
        
        if env == 'production':
            return os.getenv('PROD_DATABASE_URL') or os.getenv('DATABASE_URL')
        elif env == 'development':
            return os.getenv('DEV_DATABASE_URL') or os.getenv('DATABASE_URL')
        else:
            return os.getenv('DATABASE_URL')
    
    def _initialize_pool(self):
        """Initialize connection pool with serverless-optimized settings"""
        database_url = self._get_database_url()
        
        if not database_url:
            raise ValueError("No database URL configured")
        
        # Serverless-optimized pool settings
        min_connections = int(os.getenv('DATABASE_POOL_MIN', '1'))
        max_connections = int(os.getenv('DATABASE_POOL_SIZE', '10'))
        
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                min_connections,
                max_connections,
                database_url,
                cursor_factory=RealDictCursor,
                # Serverless optimizations
                connect_timeout=int(os.getenv('DATABASE_POOL_TIMEOUT', '10')),
                keepalives_idle=int(os.getenv('DATABASE_KEEPALIVE_IDLE', '300')),
                keepalives_interval=int(os.getenv('DATABASE_KEEPALIVE_INTERVAL', '30')),
                keepalives_count=int(os.getenv('DATABASE_KEEPALIVE_COUNT', '3')),
            )
            logger.info(f"Database connection pool initialized with {min_connections}-{max_connections} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = self.connection_pool.getconn()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                self.connection_pool.putconn(connection)
    
    @contextmanager
    def get_cursor(self, commit=True):
        """Context manager for database cursors with automatic transaction handling"""
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                yield cursor
                if commit:
                    connection.commit()
            except Exception as e:
                connection.rollback()
                logger.error(f"Database cursor error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = True) -> Any:
        """Execute a query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all and cursor.description:
                return cursor.fetchall()
            else:
                return cursor.rowcount
    
    def close_pool(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()

class SymbolManager:
    """Manage stock symbols in the database"""
    
    @staticmethod
    def get_all_symbols() -> List[Dict[str, str]]:
        """Get all symbols from database"""
        query = "SELECT symbol, company_name FROM symbols ORDER BY symbol"
        return db_manager.execute_query(query)
    
    @staticmethod
    def add_symbol(symbol: str, company_name: str) -> bool:
        """Add a new symbol to database"""
        try:
            query = """
                INSERT INTO symbols (symbol, company_name) 
                VALUES (%s, %s) 
                ON CONFLICT (symbol) DO UPDATE SET 
                    company_name = EXCLUDED.company_name,
                    updated_at = NOW()
            """
            db_manager.execute_query(query, (symbol, company_name))
            return True
        except Exception as e:
            logger.error(f"Failed to add symbol {symbol}: {e}")
            return False
    
    @staticmethod
    def bulk_add_symbols(symbols: List[Tuple[str, str]]) -> int:
        """Bulk add symbols to database"""
        query = """
            INSERT INTO symbols (symbol, company_name) 
            VALUES %s 
            ON CONFLICT (symbol) DO UPDATE SET 
                company_name = EXCLUDED.company_name,
                updated_at = NOW()
        """
        try:
            with db_manager.get_cursor() as cursor:
                from psycopg2.extras import execute_values
                execute_values(cursor, query, symbols, template=None, page_size=100)
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to bulk add symbols: {e}")
            return 0

class PriceDataManager:
    """Manage daily price data in the database"""
    
    @staticmethod
    def get_price_data(symbol: str, days: int = 30) -> List[Dict]:
        """Get price data for a symbol"""
        query = """
            SELECT date, open, high, low, close, adj_close, volume
            FROM daily_prices 
            WHERE symbol = %s AND date >= %s
            ORDER BY date DESC
            LIMIT %s
        """
        start_date = datetime.now().date() - timedelta(days=days)
        return db_manager.execute_query(query, (symbol, start_date, days * 2))
    
    @staticmethod
    def add_price_data(symbol: str, date: str, open_price: float, high: float, 
                      low: float, close: float, adj_close: float = None, volume: int = None) -> bool:
        """Add price data for a symbol"""
        try:
            query = """
                INSERT INTO daily_prices (symbol, date, open, high, low, close, adj_close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    adj_close = EXCLUDED.adj_close,
                    volume = EXCLUDED.volume,
                    updated_at = NOW()
            """
            db_manager.execute_query(query, (symbol, date, open_price, high, low, close, adj_close, volume))
            return True
        except Exception as e:
            logger.error(f"Failed to add price data for {symbol}: {e}")
            return False

class CacheManager:
    """Database-based cache manager (replaces Redis)"""
    
    @staticmethod
    def get(key: str) -> Optional[str]:
        """Get value from cache"""
        query = """
            SELECT value FROM cache_entries 
            WHERE key = %s AND (expires_at IS NULL OR expires_at > NOW())
        """
        result = db_manager.execute_query(query, (key,), fetch_one=True)
        return result['value'] if result else None
    
    @staticmethod
    def set(key: str, value: str, timeout: int = None) -> bool:
        """Set value in cache with optional timeout"""
        try:
            expires_at = None
            if timeout:
                expires_at = datetime.now() + timedelta(seconds=timeout)
            
            query = """
                INSERT INTO cache_entries (key, value, expires_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
            """
            db_manager.execute_query(query, (key, value, expires_at))
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache"""
        try:
            query = "DELETE FROM cache_entries WHERE key = %s"
            db_manager.execute_query(query, (key,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    @staticmethod
    def clear_expired():
        """Clear expired cache entries"""
        try:
            query = "SELECT clean_expired_cache()"
            result = db_manager.execute_query(query, fetch_one=True)
            count = list(result.values())[0] if result else 0
            logger.info(f"Cleared {count} expired cache entries")
            return count
        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
            return 0

class RateLimitManager:
    """Database-based rate limiting (replaces Redis)"""
    
    @staticmethod
    def is_rate_limited(identifier: str, limit: int, window: int) -> Tuple[bool, int]:
        """Check if identifier is rate limited. Returns (is_limited, remaining_count)"""
        try:
            reset_time = datetime.now() + timedelta(seconds=window)
            
            # Get or create rate limit entry
            query = """
                INSERT INTO rate_limits (identifier, count, reset_time)
                VALUES (%s, 1, %s)
                ON CONFLICT (identifier) DO UPDATE SET
                    count = CASE 
                        WHEN rate_limits.reset_time < NOW() THEN 1
                        ELSE rate_limits.count + 1
                    END,
                    reset_time = CASE
                        WHEN rate_limits.reset_time < NOW() THEN %s
                        ELSE rate_limits.reset_time
                    END,
                    updated_at = NOW()
                RETURNING count, reset_time
            """
            
            result = db_manager.execute_query(query, (identifier, reset_time, reset_time), fetch_one=True)
            
            if result:
                count = result['count']
                is_limited = count > limit
                remaining = max(0, limit - count)
                return is_limited, remaining
            
            return False, limit - 1
            
        except Exception as e:
            logger.error(f"Failed to check rate limit for {identifier}: {e}")
            return False, limit  # Fail open
    
    @staticmethod
    def clear_expired():
        """Clear expired rate limit entries"""
        try:
            query = "SELECT clean_expired_rate_limits()"
            result = db_manager.execute_query(query, fetch_one=True)
            count = list(result.values())[0] if result else 0
            logger.info(f"Cleared {count} expired rate limit entries")
            return count
        except Exception as e:
            logger.error(f"Failed to clear expired rate limits: {e}")
            return 0

def health_check() -> Dict[str, Any]:
    """Perform database health check"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        return {
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def cleanup_expired_data():
    """Clean up expired cache and rate limit data"""
    try:
        cache_cleaned = CacheManager.clear_expired()
        rate_limits_cleaned = RateLimitManager.clear_expired()
        
        logger.info(f"Cleanup completed: {cache_cleaned} cache entries, {rate_limits_cleaned} rate limits")
        return cache_cleaned + rate_limits_cleaned
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 0