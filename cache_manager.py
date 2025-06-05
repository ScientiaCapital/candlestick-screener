from typing import Any, Optional, Dict, Callable
from functools import wraps
from flask_caching import Cache
import logging
from config import Config

logger = logging.getLogger(__name__)

# Initialize cache
cache = Cache()

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from prefix and arguments"""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)

def cache_stock_data(ttl: int = 3600):
    """Cache decorator for stock data"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, symbol: str, *args, **kwargs):
            try:
                cache_key = get_cache_key('stock_data', symbol, *args, **kwargs)
                result = cache.get(cache_key)
                
                if result is None:
                    logger.debug(f"Cache miss for stock data: {symbol}")
                    result = func(self, symbol, *args, **kwargs)
                    if result is not None and not result.empty:
                        cache.set(cache_key, result, timeout=ttl)
                        logger.debug(f"Cached stock data for: {symbol}")
                else:
                    logger.debug(f"Cache hit for stock data: {symbol}")
                
                return result
            except Exception as e:
                logger.error(f"Cache error for stock data {symbol}: {str(e)}")
                # Fallback to direct function call if cache fails
                return func(self, symbol, *args, **kwargs)
        return wrapper
    return decorator

def cache_pattern_analysis(ttl: int = 900):
    """Cache decorator for pattern analysis"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cache_key = get_cache_key('pattern_analysis', *args, **kwargs)
                result = cache.get(cache_key)
                
                if result is None:
                    logger.debug(f"Cache miss for pattern analysis: {cache_key}")
                    result = func(*args, **kwargs)
                    if result is not None:
                        cache.set(cache_key, result, timeout=ttl)
                        logger.debug(f"Cached pattern analysis: {cache_key}")
                else:
                    logger.debug(f"Cache hit for pattern analysis: {cache_key}")
                
                return result
            except Exception as e:
                logger.error(f"Cache error for pattern analysis: {str(e)}")
                # Fallback to direct function call if cache fails
                return func(*args, **kwargs)
        return wrapper
    return decorator

def cache_symbol_list(ttl: int = 86400):
    """Cache decorator for symbol list"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cache_key = get_cache_key('symbols', 'list', *args, **kwargs)
                result = cache.get(cache_key)
                
                if result is None:
                    logger.debug("Cache miss for symbol list")
                    result = func(*args, **kwargs)
                    if result is not None:
                        cache.set(cache_key, result, timeout=ttl)
                        logger.debug(f"Cached symbol list with {len(result)} symbols")
                else:
                    logger.debug(f"Cache hit for symbol list with {len(result)} symbols")
                
                return result
            except Exception as e:
                logger.error(f"Cache error for symbol list: {str(e)}")
                # Fallback to direct function call if cache fails
                return func(*args, **kwargs)
        return wrapper
    return decorator

def invalidate_cache(prefix: str, *args, **kwargs):
    """Invalidate cache entries matching the prefix and arguments"""
    try:
        cache_key = get_cache_key(prefix, *args, **kwargs)
        cache.delete(cache_key)
        logger.debug(f"Invalidated cache key: {cache_key}")
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")

def invalidate_pattern_cache(pattern: str):
    """Invalidate all cached pattern analysis for a specific pattern"""
    try:
        # This is a simplified approach - in production you might want
        # to use Redis SCAN to find and delete matching keys
        cache.clear()
        logger.info(f"Cleared all cache due to pattern invalidation: {pattern}")
    except Exception as e:
        logger.error(f"Error invalidating pattern cache: {str(e)}")

def warm_cache():
    """Warm up the cache with commonly accessed data"""
    try:
        from app import load_symbols
        logger.info("Warming up cache with symbol list")
        load_symbols()
    except Exception as e:
        logger.error(f"Error warming cache: {str(e)}")

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    try:
        # Basic cache statistics
        stats = {
            'type': Config.CACHE_TYPE,
            'timeout': Config.CACHE_TIMEOUT,
            'redis_url': Config.CACHE_REDIS_URL if Config.CACHE_TYPE == 'redis' else None,
            'status': 'connected'
        }
        
        # Try to test cache connectivity
        test_key = 'cache_test_key'
        cache.set(test_key, 'test_value', timeout=1)
        test_result = cache.get(test_key)
        cache.delete(test_key)
        
        if test_result != 'test_value':
            stats['status'] = 'error'
            stats['error'] = 'Cache test failed'
            
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {
            'type': Config.CACHE_TYPE,
            'status': 'error',
            'error': str(e)
        } 