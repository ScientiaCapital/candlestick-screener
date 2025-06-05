import pytest
from unittest.mock import Mock, patch
from rate_limiter import (
    limiter, limit_snapshot, limit_pattern_analysis,
    limit_index, limit_burst, get_rate_limit_stats
)

def test_rate_limit_decorators():
    """Test rate limit decorators"""
    # Test snapshot limit
    snapshot_limit = limit_snapshot()
    assert str(snapshot_limit) == "10/hour"

    # Test pattern analysis limit
    pattern_limit = limit_pattern_analysis()
    assert str(pattern_limit) == "100/hour"

    # Test index limit
    index_limit = limit_index()
    assert str(index_limit) == "200/hour"

    # Test burst limit
    burst_limit = limit_burst()
    assert str(burst_limit) == "50/minute"

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

    # Verify limiter was called with correct limits
    assert mock_limiter.limit.call_count == 4
    calls = [call[0][0] for call in mock_limiter.limit.call_args_list]
    assert "10/hour" in calls
    assert "100/hour" in calls
    assert "200/hour" in calls
    assert "50/minute" in calls

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
    # Mock limiter response
    mock_response = Mock()
    mock_response.headers = {
        'X-RateLimit-Limit': '200',
        'X-RateLimit-Remaining': '199',
        'X-RateLimit-Reset': '1234567890'
    }
    mock_limiter.limit.return_value = lambda x: mock_response

    # Test function with limit
    @limit_index()
    def test_function():
        return "test"

    # Verify headers
    response = test_function()
    assert response.headers['X-RateLimit-Limit'] == '200'
    assert response.headers['X-RateLimit-Remaining'] == '199'
    assert response.headers['X-RateLimit-Reset'] == '1234567890' 