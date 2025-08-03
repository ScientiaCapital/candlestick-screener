import os
import pytest
from config import Config

def test_default_config():
    """Test default configuration values"""
    assert Config.FLASK_APP == 'app.py'
    assert Config.FLASK_ENV == 'development'
    assert Config.FLASK_DEBUG is True
    assert Config.BATCH_SIZE == 10
    assert Config.CACHE_TYPE == 'simple'  # Updated to match current default
    assert Config.CACHE_REDIS_URL == 'redis://localhost:6379/0'
    assert Config.CACHE_TIMEOUT == 300
    assert Config.RATELIMIT_DEFAULT == '200/hour'

def test_config_validation():
    """Test configuration validation"""
    # Test with default values in development (should have warnings)
    result = Config.validate()
    # In development mode, SECRET_KEY is auto-generated, so no errors
    # But there should be warnings for missing API keys
    if 'warnings' in result:
        assert 'ALPHA_VANTAGE_API_KEY' in result['warnings']

    # Test with valid values
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['ALPHA_VANTAGE_API_KEY'] = 'test-api-key'
    result = Config.validate()
    # With valid values, no errors expected
    assert 'errors' not in result or not result['errors']

def test_cache_config():
    """Test cache configuration"""
    cache_config = Config.get_cache_config()
    assert cache_config['CACHE_TYPE'] == Config.CACHE_TYPE
    assert cache_config['CACHE_REDIS_URL'] == Config.CACHE_REDIS_URL
    assert cache_config['CACHE_TIMEOUT'] == Config.CACHE_TIMEOUT

def test_rate_limit_config():
    """Test rate limit configuration"""
    rate_limit_config = Config.get_rate_limit_config()
    assert rate_limit_config['RATELIMIT_STORAGE_URL'] == Config.RATELIMIT_STORAGE_URL
    assert rate_limit_config['RATELIMIT_DEFAULT'] == Config.RATELIMIT_DEFAULT
    assert rate_limit_config['RATELIMIT_STORAGE_OPTIONS'] == Config.RATELIMIT_STORAGE_OPTIONS 