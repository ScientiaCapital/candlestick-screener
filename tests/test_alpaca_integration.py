"""
Test Alpaca integration using TDD methodology
Tests for official alpaca-py SDK integration with yfinance-compatible data format
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import os

# Import the modules we'll test
from alpaca_client_sdk import AlpacaSDKClient, get_alpaca_client
from patterns import candlestick_patterns


def create_mock_bar_data():
    """Helper function to create mock bar data for testing"""
    mock_bar = Mock()
    mock_bar.timestamp = pd.Timestamp('2024-01-01')
    mock_bar.open = 150.0
    mock_bar.high = 155.0
    mock_bar.low = 149.0
    mock_bar.close = 154.0
    mock_bar.volume = 1000000
    return mock_bar


def setup_mock_response(mock_client, symbol='AAPL', num_bars=5):
    """Helper function to set up mock API response"""
    mock_bars = []
    for i in range(num_bars):
        mock_bar = create_mock_bar_data()
        # Fix date formatting - pad with zeros correctly
        day = str(i+1).zfill(2)  # This will give us '01', '02', etc.
        mock_bar.timestamp = pd.Timestamp(f'2024-01-{day}')
        mock_bar.open = 150.0 + i
        mock_bar.high = 155.0 + i
        mock_bar.low = 149.0 + i
        mock_bar.close = 154.0 + i
        mock_bars.append(mock_bar)
    
    mock_response = Mock()
    mock_response.data = {symbol: mock_bars}
    
    # Patch the client method correctly
    mock_client.client.get_stock_bars = Mock(return_value=mock_response)
    return mock_response


class TestAlpacaSDKClient:
    """Test Alpaca SDK client initialization and basic functionality"""
    
    def test_alpaca_client_initialization_requires_credentials(self):
        """Test that Alpaca client initialization requires API credentials"""
        # This test should fail initially - we need credentials to initialize
        with patch.dict(os.environ, {'ALPACA_API_KEY': '', 'ALPACA_SECRET_KEY': ''}):
            with pytest.raises(ValueError, match="Alpaca API credentials not configured"):
                AlpacaSDKClient()
    
    def test_alpaca_client_initialization_with_valid_credentials(self):
        """Test successful Alpaca client initialization with valid credentials"""
        # Mock credentials for testing
        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'PKV759RYS7G6DTHFFQK1',
            'ALPACA_SECRET_KEY': 'hQI5lHekr89ilSVAgCbJCOP4EcsqtuGMeKpN'
        }):
            client = AlpacaSDKClient()
            assert client is not None
            assert hasattr(client, 'api_key')
            assert hasattr(client, 'secret_key')
            assert client.api_key == 'PKV759RYS7G6DTHFFQK1'
    
    def test_get_alpaca_client_singleton(self):
        """Test that get_alpaca_client returns a singleton instance"""
        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'PKV759RYS7G6DTHFFQK1',
            'ALPACA_SECRET_KEY': 'hQI5lHekr89ilSVAgCbJCOP4EcsqtuGMeKpN'
        }):
            client1 = get_alpaca_client()
            client2 = get_alpaca_client()
            assert client1 is client2


class TestAlpacaDataFetching:
    """Test fetching historical data from Alpaca API"""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Alpaca client for testing"""
        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'PKV759RYS7G6DTHFFQK1',
            'ALPACA_SECRET_KEY': 'hQI5lHekr89ilSVAgCbJCOP4EcsqtuGMeKpN'
        }):
            return AlpacaSDKClient()
    
    @patch('alpaca_client_sdk.StockHistoricalDataClient')
    def test_fetch_historical_data_for_aapl(self, mock_stock_client, mock_client):
        """Test fetching historical data for AAPL using official alpaca-py SDK"""
        # Set up mock response
        setup_mock_response(mock_client, 'AAPL', 5)
        
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        data = mock_client.get_stock_data('AAPL', start_date, end_date)
        
        # Verify we get data back
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
    
    def test_invalid_symbol_returns_none(self, mock_client):
        """Test that invalid symbols return None"""
        data = mock_client.get_stock_data('INVALID_SYMBOL_123')
        assert data is None
    
    def test_empty_symbol_returns_none(self, mock_client):
        """Test that empty or None symbols return None"""
        assert mock_client.get_stock_data('') is None
        assert mock_client.get_stock_data(None) is None


class TestDataFormatCompatibility:
    """Test that Alpaca data format matches yfinance structure"""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Alpaca client for testing"""
        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'PKV759RYS7G6DTHFFQK1',
            'ALPACA_SECRET_KEY': 'hQI5lHekr89ilSVAgCbJCOP4EcsqtuGMeKpN'
        }):
            return AlpacaSDKClient()
    
    @patch('alpaca_client_sdk.StockHistoricalDataClient')
    def test_data_format_has_required_columns(self, mock_stock_client, mock_client):
        """Test that returned data has required OHLCV columns matching yfinance"""
        # Set up mock response
        setup_mock_response(mock_client, 'AAPL', 5)
        
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        data = mock_client.get_stock_data('AAPL', start_date, end_date)
        
        # Verify column structure matches yfinance
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        assert all(col in data.columns for col in required_columns)
    
    @patch('alpaca_client_sdk.StockHistoricalDataClient')
    def test_data_format_has_datetime_index(self, mock_stock_client, mock_client):
        """Test that returned data has datetime index like yfinance"""
        # Set up mock response
        setup_mock_response(mock_client, 'AAPL', 5)
        
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        data = mock_client.get_stock_data('AAPL', start_date, end_date)
        
        # Verify datetime index
        assert isinstance(data.index, pd.DatetimeIndex)
    
    @patch('alpaca_client_sdk.StockHistoricalDataClient')
    def test_data_format_numeric_types(self, mock_stock_client, mock_client):
        """Test that OHLC data are numeric types and Volume is integer"""
        # Set up mock response
        setup_mock_response(mock_client, 'AAPL', 5)
        
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        data = mock_client.get_stock_data('AAPL', start_date, end_date)
        
        # Verify data types
        assert pd.api.types.is_numeric_dtype(data['Open'])
        assert pd.api.types.is_numeric_dtype(data['High'])
        assert pd.api.types.is_numeric_dtype(data['Low'])
        assert pd.api.types.is_numeric_dtype(data['Close'])
        assert pd.api.types.is_integer_dtype(data['Volume'])
    
    @patch('alpaca_client_sdk.StockHistoricalDataClient')
    def test_ohlc_data_consistency(self, mock_stock_client, mock_client):
        """Test that OHLC data follows basic market rules"""
        # Set up mock response
        setup_mock_response(mock_client, 'AAPL', 5)
        
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        data = mock_client.get_stock_data('AAPL', start_date, end_date)
        
        # Basic OHLC validation: High >= Open, Close, Low <= Open, Close
        assert (data['High'] >= data['Open']).all()
        assert (data['High'] >= data['Close']).all()
        assert (data['Low'] <= data['Open']).all()
        assert (data['Low'] <= data['Close']).all()


class TestPatternDetectionWithAlpacaData:
    """Test that existing pattern detection works with Alpaca data"""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Alpaca client for testing"""
        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'PKV759RYS7G6DTHFFQK1',
            'ALPACA_SECRET_KEY': 'hQI5lHekr89ilSVAgCbJCOP4EcsqtuGMeKpN'
        }):
            return AlpacaSDKClient()
    
    @patch('alpaca_client_sdk.StockHistoricalDataClient')
    @patch('pandas_ta.cdl')
    def test_doji_pattern_detection_with_alpaca_data(self, mock_cdl, mock_stock_client, mock_client):
        """Test that CDLDOJI pattern detection works with Alpaca data"""
        from app import PatternAnalyzer
        
        # Set up mock response with more data points for pattern detection
        setup_mock_response(mock_client, 'AAPL', 20)
        
        # Mock the pattern detection function
        mock_pattern_func = Mock()
        mock_pattern_func.return_value = pd.Series([0, 100, 0, -100, 0] * 4, name='CDLDOJI')
        mock_cdl.doji = mock_pattern_func
        
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Get Alpaca data
        data = mock_client.get_stock_data('AAPL', start_date, end_date)
        assert data is not None
        
        # Test pattern detection
        analyzer = PatternAnalyzer()
        pattern_result = analyzer.process_pattern(data, 'CDLDOJI')
        
        # Verify pattern detection works
        assert pattern_result is not None
        assert isinstance(pattern_result, pd.Series)
        assert len(pattern_result) == len(data)
    
    @patch('alpaca_client_sdk.StockHistoricalDataClient')
    @patch('pandas_ta.cdl')
    def test_hammer_pattern_detection_with_alpaca_data(self, mock_cdl, mock_stock_client, mock_client):
        """Test that CDLHAMMER pattern detection works with Alpaca data"""
        from app import PatternAnalyzer
        
        # Set up mock response with more data points for pattern detection
        setup_mock_response(mock_client, 'AAPL', 20)
        
        # Mock the pattern detection function
        mock_pattern_func = Mock()
        mock_pattern_func.return_value = pd.Series([0, 100, 0, -100, 0] * 4, name='CDLHAMMER')
        mock_cdl.hammer = mock_pattern_func
        
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Get Alpaca data
        data = mock_client.get_stock_data('AAPL', start_date, end_date)
        assert data is not None
        
        # Test pattern detection
        analyzer = PatternAnalyzer()
        pattern_result = analyzer.process_pattern(data, 'CDLHAMMER')
        
        # Verify pattern detection works
        assert pattern_result is not None
        assert isinstance(pattern_result, pd.Series)
        assert len(pattern_result) == len(data)
    
    @patch('alpaca_client_sdk.StockHistoricalDataClient')
    @patch('pandas_ta.cdl')
    def test_batch_pattern_processing_with_alpaca_data(self, mock_cdl, mock_stock_client, mock_client):
        """Test batch processing of multiple patterns with Alpaca data"""
        from app import PatternAnalyzer
        
        # Set up mock response with more data points for pattern detection
        setup_mock_response(mock_client, 'AAPL', 20)
        
        # Mock the pattern detection functions
        mock_doji = Mock()
        mock_doji.return_value = pd.Series([0, 100, 0, -100, 0] * 4, name='CDLDOJI')
        mock_cdl.doji = mock_doji
        
        mock_hammer = Mock()
        mock_hammer.return_value = pd.Series([0, 0, 100, 0, -100] * 4, name='CDLHAMMER')
        mock_cdl.hammer = mock_hammer
        
        mock_engulfing = Mock()
        mock_engulfing.return_value = pd.Series([100, 0, 0, -100, 0] * 4, name='CDLENGULFING')
        mock_cdl.engulfing = mock_engulfing
        
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Get Alpaca data
        data = mock_client.get_stock_data('AAPL', start_date, end_date)
        assert data is not None
        
        # Test batch pattern processing
        analyzer = PatternAnalyzer()
        test_patterns = ['CDLDOJI', 'CDLHAMMER', 'CDLENGULFING']
        results = analyzer.batch_process_patterns(data, test_patterns)
        
        # Verify results
        assert isinstance(results, dict)
        assert len(results) > 0
        for pattern in test_patterns:
            if pattern in results:
                assert isinstance(results[pattern], pd.Series)
                assert len(results[pattern]) == len(data)


class TestAlpacaConnectionAndAuth:
    """Test Alpaca API connection and authentication"""
    
    def test_connection_test_method_exists(self):
        """Test that connection test method exists and works"""
        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'PKV759RYS7G6DTHFFQK1',
            'ALPACA_SECRET_KEY': 'hQI5lHekr89ilSVAgCbJCOP4EcsqtuGMeKpN'
        }):
            client = AlpacaSDKClient()
            # This should work without throwing an exception
            connection_status = client.test_connection()
            assert isinstance(connection_status, bool)
    
    def test_connection_fails_with_invalid_credentials(self):
        """Test that connection fails with invalid credentials"""
        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'invalid_key',
            'ALPACA_SECRET_KEY': 'invalid_secret'
        }):
            client = AlpacaSDKClient()
            connection_status = client.test_connection()
            assert connection_status is False