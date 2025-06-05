import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from app import app, StockDataManager, PatternAnalyzer

@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Test the index route"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Technical Scanner' in response.data

def test_snapshot_route(client):
    """Test the snapshot route"""
    with patch('app.StockDataManager.get_stock_data') as mock_get_data:
        mock_get_data.return_value = pd.DataFrame({'data': [1, 2, 3]})
        response = client.get('/snapshot')
        assert response.status_code == 200
        assert b'success' in response.data.lower()

def test_stats_route(client):
    """Test the stats route"""
    response = client.get('/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert 'cache' in data
    assert 'rate_limits' in data

def test_stock_data_manager():
    """Test StockDataManager class"""
    manager = StockDataManager()
    
    # Test symbol validation
    assert manager.validate_symbol('AAPL') is True
    assert manager.validate_symbol('') is False
    assert manager.validate_symbol('123') is True
    assert manager.validate_symbol('A@PL') is False

    # Test get_stock_data with mock
    with patch('yfinance.download') as mock_download:
        mock_download.return_value = pd.DataFrame({'data': [1, 2, 3]})
        data = manager.get_stock_data('AAPL')
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 3

def test_pattern_analyzer():
    """Test PatternAnalyzer class"""
    analyzer = PatternAnalyzer()
    
    # Test pattern signal
    assert analyzer.get_pattern_signal(1) == 'bullish'
    assert analyzer.get_pattern_signal(-1) == 'bearish'
    assert analyzer.get_pattern_signal(0) is None
    
    # Test batch processing with mock
    df = pd.DataFrame({
        'Open': [1, 2, 3],
        'High': [2, 3, 4],
        'Low': [0, 1, 2],
        'Close': [1.5, 2.5, 3.5]
    })
    
    # Mock pandas-ta's cdl_pattern method
    with patch('pandas.DataFrame.ta.cdl_pattern') as mock_pattern:
        mock_pattern.return_value = pd.Series([1, -1, 0])
        results = analyzer.batch_process_patterns(df, ['CDLDOJI'])
        assert 'CDLDOJI' in results
        assert isinstance(results['CDLDOJI'], pd.Series)

def test_invalid_pattern(client):
    """Test invalid pattern handling"""
    response = client.get('/?pattern=INVALID')
    assert response.status_code == 200
    assert b'Invalid pattern selected' in response.data

def test_caching_decorators():
    """Test that caching decorators are applied"""
    from cache_manager import cache
    manager = StockDataManager()
    analyzer = PatternAnalyzer()
    df = pd.DataFrame({
        'Open': [1], 'High': [2], 'Low': [1], 'Close': [1.5]
    })

    with patch.object(cache, 'get', return_value=None) as mock_get, \
         patch.object(cache, 'set') as mock_set:
        # Test stock data caching
        manager.get_stock_data('AAPL')
        assert mock_get.called
        assert mock_set.called

        # Test pattern analysis caching
        analyzer.batch_process_patterns(df, ['CDLDOJI'])
        assert mock_get.called
        assert mock_set.called

        # Test symbol list caching
        from app import load_symbols
        load_symbols()
        assert mock_get.called
        assert mock_set.called

@patch('rate_limiter.limiter')
def test_rate_limit_decorators(mock_limiter, client):
    """Test that rate limit decorators are applied"""
    # Configure mock limiter
    mock_limiter.limit.return_value = lambda f: f
    
    with app.test_request_context():
        # Test snapshot rate limit
        response = client.get('/snapshot')
        assert response.status_code == 200
        mock_limiter.limit.assert_any_call("10/hour")

        # Test index rate limit
        response = client.get('/')
        assert response.status_code == 200
        mock_limiter.limit.assert_any_call("200/hour")

        # Test stats rate limit
        response = client.get('/stats')
        assert response.status_code == 200
        mock_limiter.limit.assert_any_call("50/minute") 