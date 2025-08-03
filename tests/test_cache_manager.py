import pytest
from unittest.mock import Mock, patch
import pandas as pd
from cache_manager import (
    get_cache_key, cache_stock_data, cache_pattern_analysis,
    cache_symbol_list, invalidate_cache, get_cache_stats
)

def test_get_cache_key():
    """Test cache key generation"""
    # Test with simple arguments
    key = get_cache_key('test', 'arg1', 'arg2')
    assert key == 'test:arg1:arg2'

    # Test with keyword arguments
    key = get_cache_key('test', arg1='value1', arg2='value2')
    assert key == 'test:arg1:value1:arg2:value2'

    # Test with mixed arguments
    key = get_cache_key('test', 'arg1', arg2='value2')
    assert key == 'test:arg1:arg2:value2'

@patch('cache_manager.cache')
def test_cache_stock_data(mock_cache):
    """Test stock data caching"""
    # Mock cache get/set
    mock_cache.get.return_value = None
    mock_cache.set = Mock()

    # Test class with method (since cache_stock_data expects self parameter)
    class TestDataManager:
        @cache_stock_data()
        def get_data(self, symbol):
            return pd.DataFrame({'data': [1, 2, 3]})

    manager = TestDataManager()

    # Test cache miss
    result = manager.get_data('AAPL')
    assert result is not None
    mock_cache.get.assert_called_once()
    mock_cache.set.assert_called_once()

    # Test cache hit
    mock_cache.get.return_value = pd.DataFrame({'data': [4, 5, 6]})
    result = manager.get_data('AAPL')
    assert result is not None
    assert len(mock_cache.set.call_args_list) == 1  # Should not set again

@patch('cache_manager.cache')
def test_cache_pattern_analysis(mock_cache):
    """Test pattern analysis caching"""
    # Mock cache get/set
    mock_cache.get.return_value = None
    mock_cache.set = Mock()

    # Test function
    @cache_pattern_analysis()
    def analyze_pattern(symbol, pattern):
        return {'result': 'test'}

    # Test cache miss
    result = analyze_pattern('AAPL', 'CDLDOJI')
    assert result is not None
    mock_cache.get.assert_called_once()
    mock_cache.set.assert_called_once()

    # Test cache hit
    mock_cache.get.return_value = {'result': 'cached'}
    result = analyze_pattern('AAPL', 'CDLDOJI')
    assert result == {'result': 'cached'}
    assert len(mock_cache.set.call_args_list) == 1  # Should not set again

@patch('cache_manager.cache')
def test_cache_symbol_list(mock_cache):
    """Test symbol list caching"""
    # Mock cache get/set
    mock_cache.get.return_value = None
    mock_cache.set = Mock()

    # Test function
    @cache_symbol_list()
    def get_symbols():
        return {'AAPL': {'company': 'Apple Inc.'}}

    # Test cache miss
    result = get_symbols()
    assert result is not None
    mock_cache.get.assert_called_once()
    mock_cache.set.assert_called_once()

    # Test cache hit
    mock_cache.get.return_value = {'MSFT': {'company': 'Microsoft Corp.'}}
    result = get_symbols()
    assert result == {'MSFT': {'company': 'Microsoft Corp.'}}
    assert len(mock_cache.set.call_args_list) == 1  # Should not set again

@patch('cache_manager.cache')
def test_invalidate_cache(mock_cache):
    """Test cache invalidation"""
    mock_cache.delete = Mock()
    
    # Test invalidation
    invalidate_cache('test', 'arg1', 'arg2')
    mock_cache.delete.assert_called_once_with('test:arg1:arg2')

def test_get_cache_stats():
    """Test cache statistics"""
    stats = get_cache_stats()
    assert 'type' in stats
    assert 'timeout' in stats
    assert 'redis_url' in stats 