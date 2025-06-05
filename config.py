import os
import secrets
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Generate a secure secret key if none is provided
def generate_secret_key() -> str:
    return secrets.token_urlsafe(32)

class Config:
    """Application configuration class"""
    
    # Flask settings
    FLASK_APP = os.getenv('FLASK_APP', 'app.py')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Secret key handling
    _secret_key = os.getenv('SECRET_KEY')
    if not _secret_key and FLASK_ENV == 'production':
        raise ValueError("SECRET_KEY must be set in production")
    SECRET_KEY = _secret_key or generate_secret_key()
    
    # Data processing
    BATCH_SIZE = max(1, min(50, int(os.getenv('BATCH_SIZE', '10'))))  # Limit batch size
    MAX_SYMBOLS = int(os.getenv('MAX_SYMBOLS', '1000'))  # Limit number of symbols
    
    # Cache settings
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'redis')
    CACHE_REDIS_URL = os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TIMEOUT = max(60, int(os.getenv('CACHE_TIMEOUT', '300')))  # Minimum 1 minute
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/0')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200/hour')
    RATELIMIT_STORAGE_OPTIONS = {
        'socket_connect_timeout': 30,
        'socket_timeout': 30
    }
    
    # API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    # Security settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return any issues"""
        issues = {}
        warnings = {}
        
        # Critical validations (production errors)
        if cls.FLASK_ENV == 'production':
            if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key':
                issues['SECRET_KEY'] = 'Production secret key not set'
                
            if cls.FLASK_DEBUG:
                issues['FLASK_DEBUG'] = 'Debug mode should be disabled in production'
                
        # Warning validations
        if not cls.ALPHA_VANTAGE_API_KEY:
            warnings['ALPHA_VANTAGE_API_KEY'] = 'Alpha Vantage API key not set - yfinance will be used'
            
        # Validate Redis connection
        if cls.CACHE_TYPE == 'redis' and not cls.CACHE_REDIS_URL:
            warnings['CACHE_REDIS_URL'] = 'Redis URL not set - using memory cache'
            
        # Validate batch size
        if cls.BATCH_SIZE > 50:
            warnings['BATCH_SIZE'] = 'Large batch size may impact performance'
            
        result = {}
        if issues:
            result['errors'] = issues
        if warnings:
            result['warnings'] = warnings
            
        return result
    
    @classmethod
    def get_cache_config(cls) -> Dict[str, Any]:
        """Get cache configuration"""
        return {
            'CACHE_TYPE': cls.CACHE_TYPE,
            'CACHE_REDIS_URL': cls.CACHE_REDIS_URL,
            'CACHE_TIMEOUT': cls.CACHE_TIMEOUT
        }
    
    @classmethod
    def get_rate_limit_config(cls) -> Dict[str, Any]:
        """Get rate limit configuration"""
        return {
            'RATELIMIT_STORAGE_URL': cls.RATELIMIT_STORAGE_URL,
            'RATELIMIT_DEFAULT': cls.RATELIMIT_DEFAULT,
            'RATELIMIT_STORAGE_OPTIONS': cls.RATELIMIT_STORAGE_OPTIONS
        }
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return cls.FLASK_ENV == 'production'
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': cls.LOG_LEVEL,
            'file': cls.LOG_FILE,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        } 