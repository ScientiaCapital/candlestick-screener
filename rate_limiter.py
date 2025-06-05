from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from config import Config

logger = logging.getLogger(__name__)

# Initialize rate limiter
try:
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=Config.RATELIMIT_STORAGE_URL,
        storage_options=Config.RATELIMIT_STORAGE_OPTIONS,
        default_limits=[Config.RATELIMIT_DEFAULT],
        enabled=True,
        strategy="fixed-window",
        on_breach=lambda: logger.warning(f"Rate limit exceeded for {get_remote_address()}")
    )
except Exception as e:
    logger.error(f"Failed to initialize rate limiter: {str(e)}")
    # Create a fallback limiter with in-memory storage
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri="memory://",
        default_limits=[Config.RATELIMIT_DEFAULT],
        enabled=True,
        strategy="fixed-window"
    )

def init_app(app):
    """Initialize rate limiter with Flask app"""
    try:
        limiter.init_app(app)
        
        # Disable rate limiting in test and development modes if specified
        if app.config.get('TESTING') or (Config.FLASK_ENV == 'development' and not app.config.get('ENABLE_RATE_LIMITING')):
            limiter.enabled = False
            logger.info("Rate limiting disabled for testing/development")
        else:
            logger.info("Rate limiting enabled")
            
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter with app: {str(e)}")
        limiter.enabled = False

# Rate limit decorators with fallback
def safe_rate_limit(limit_string: str):
    """Safe rate limit decorator that handles errors gracefully"""
    def decorator(func):
        try:
            return limiter.limit(limit_string)(func)
        except Exception as e:
            logger.error(f"Rate limit decorator failed: {str(e)}")
            # Return the original function if rate limiting fails
            return func
    return decorator

def limit_snapshot():
    """Rate limit for snapshot endpoint - very restrictive"""
    return safe_rate_limit("5/hour;1/minute")

def limit_pattern_analysis():
    """Rate limit for pattern analysis"""
    return safe_rate_limit("100/hour;20/minute")

def limit_index():
    """Rate limit for index endpoint"""
    return safe_rate_limit("200/hour;50/minute")

def limit_burst():
    """Rate limit for burst requests"""
    return safe_rate_limit("50/minute;10/second")

def limit_api():
    """Rate limit for API endpoints"""
    return safe_rate_limit("300/hour;60/minute")

def get_rate_limit_stats():
    """Get rate limit statistics"""
    try:
        return {
            'storage_url': Config.RATELIMIT_STORAGE_URL,
            'default_limit': Config.RATELIMIT_DEFAULT,
            'storage_options': Config.RATELIMIT_STORAGE_OPTIONS,
            'enabled': limiter.enabled,
            'strategy': 'fixed-window',
            'status': 'active' if limiter.enabled else 'disabled'
        }
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        } 