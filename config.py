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
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')  # Use simple cache as fallback
    CACHE_REDIS_URL = os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TIMEOUT = max(60, int(os.getenv('CACHE_TIMEOUT', '300')))  # Minimum 1 minute
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/0')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200/hour')
    RATELIMIT_STORAGE_OPTIONS = {
        'socket_connect_timeout': 30,
        'socket_timeout': 30
    }
    
    # Alpaca API Configuration (Required for MVP)
    ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
    ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
    ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    
    # External API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    DEV_DATABASE_URL = os.getenv('DEV_DATABASE_URL')
    PROD_DATABASE_URL = os.getenv('PROD_DATABASE_URL')
    
    # Security settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    CSRF_SECRET_KEY = os.getenv('CSRF_SECRET_KEY')
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100/hour')
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    
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
                
            if not cls.ALPACA_API_KEY:
                issues['ALPACA_API_KEY'] = 'Alpaca API key required for production'
                
            if not cls.ALPACA_SECRET_KEY:
                issues['ALPACA_SECRET_KEY'] = 'Alpaca secret key required for production'
                
            if not cls.DATABASE_URL:
                issues['DATABASE_URL'] = 'Database URL required for production'
                
            if not cls.CSRF_SECRET_KEY:
                issues['CSRF_SECRET_KEY'] = 'CSRF secret key required for production'
                
        # Warning validations
        if not cls.ALPACA_API_KEY:
            warnings['ALPACA_API_KEY'] = 'Alpaca API key not set - trading features disabled'
            
        if not cls.ALPACA_SECRET_KEY:
            warnings['ALPACA_SECRET_KEY'] = 'Alpaca secret key not set - trading features disabled'
            
        if not cls.ALPHA_VANTAGE_API_KEY:
            warnings['ALPHA_VANTAGE_API_KEY'] = 'Alpha Vantage API key not set - yfinance will be used'
            
        if not cls.DATABASE_URL:
            warnings['DATABASE_URL'] = 'Database URL not set - using local data only'
            
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
    
    @classmethod
    def get_alpaca_config(cls) -> Dict[str, Any]:
        """Get Alpaca API configuration"""
        return {
            'api_key': cls.ALPACA_API_KEY,
            'secret_key': cls.ALPACA_SECRET_KEY,
            'base_url': cls.ALPACA_BASE_URL
        }
    
    @classmethod
    def get_security_config(cls) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'csrf_secret_key': cls.CSRF_SECRET_KEY,
            'api_rate_limit': cls.API_RATE_LIMIT,
            'request_timeout': cls.REQUEST_TIMEOUT,
            'cors_origins': cls.CORS_ORIGINS,
            'allowed_hosts': cls.ALLOWED_HOSTS,
            'max_content_length': cls.MAX_CONTENT_LENGTH
        } 