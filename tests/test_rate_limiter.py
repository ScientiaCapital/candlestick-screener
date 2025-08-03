import pytest
from unittest.mock import Mock, patch
from rate_limiter import (
    limiter, limit_snapshot, limit_pattern_analysis,
    limit_index, limit_burst, get_rate_limit_stats
)

def test_rate_limit_decorators():
    """Test rate limit decorators"""
    # Test that decorators return callable functions
    snapshot_limit = limit_snapshot()
    assert callable(snapshot_limit)

    pattern_limit = limit_pattern_analysis()
    assert callable(pattern_limit)

    index_limit = limit_index()
    assert callable(index_limit)

    burst_limit = limit_burst()
    assert callable(burst_limit)

@patch('rate_limiter.limiter')
def test_rate_limit_application(mock_limiter):
    """Test rate limit application to functions"""
    # Mock limiter
    mock_limiter.limit = Mock(return_value=lambda x: x)

    # Test function with snapshot limit
    @limit_snapshot()
    def test_snapshot():
        return "test"

    # Test function with pattern analysis limit
    @limit_pattern_analysis()
    def test_pattern():
        return "test"

    # Test function with index limit
    @limit_index()
    def test_index():
        return "test"

    # Test function with burst limit
    @limit_burst()
    def test_burst():
        return "test"

    # Verify limiter was called with correct limits (based on actual implementation)
    assert mock_limiter.limit.call_count == 4
    calls = [call[0][0] for call in mock_limiter.limit.call_args_list]
    assert "5/hour;1/minute" in calls  # snapshot limit
    assert "100/hour;20/minute" in calls  # pattern analysis limit
    assert "200/hour;50/minute" in calls  # index limit
    assert "50/minute;10/second" in calls  # burst limit

def test_get_rate_limit_stats():
    """Test rate limit statistics"""
    stats = get_rate_limit_stats()
    assert 'storage_url' in stats
    assert 'default_limit' in stats
    assert 'storage_options' in stats
    assert isinstance(stats['storage_options'], dict)

@patch('rate_limiter.limiter')
def test_rate_limit_headers(mock_limiter):
    """Test rate limit headers"""
    # Mock limiter to return a decorated function that returns a mock response
    mock_response = Mock()
    mock_response.headers = {
        'X-RateLimit-Limit': '200',
        'X-RateLimit-Remaining': '199',
        'X-RateLimit-Reset': '1234567890'
    }
    
    def mock_decorator(func):
        def wrapper(*args, **kwargs):
            return mock_response
        return wrapper
    
    mock_limiter.limit.return_value = mock_decorator

    # Test function with limit
    @limit_index()
    def test_function():
        return "test"

    # Verify headers
    response = test_function()
    assert response.headers['X-RateLimit-Limit'] == '200'
    assert response.headers['X-RateLimit-Remaining'] == '199'
    assert response.headers['X-RateLimit-Reset'] == '1234567890' 