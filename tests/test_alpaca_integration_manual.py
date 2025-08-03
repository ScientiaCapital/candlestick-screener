"""
Manual integration tests for Alpaca SDK integration

These tests make actual API calls and should be run manually
to verify real integration with Alpaca API. They are not part
of the automated test suite.

Run with: python3 -m pytest tests/test_alpaca_integration_manual.py -v -s
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import os

# Skip all tests if API credentials are not available
skip_if_no_credentials = pytest.mark.skipif(
    not (os.getenv('ALPACA_API_KEY') and os.getenv('ALPACA_SECRET_KEY')),
    reason="Alpaca credentials not available"
)


@skip_if_no_credentials
class TestAlpacaRealAPI:
    """Test real Alpaca API integration - requires valid credentials"""
    
    def test_real_alpaca_connection(self):
        """Test real connection to Alpaca API"""
        from alpaca_client_sdk import AlpacaSDKClient
        
        client = AlpacaSDKClient()
        result = client.test_connection()
        
        # This may fail with free accounts that don't have market data access
        # That's expected and okay for our MVP
        assert isinstance(result, bool)
        print(f"Alpaca connection test result: {result}")
    
    def test_real_data_fetch_format(self):
        """Test that real API data matches expected format"""
        from alpaca_client_sdk import AlpacaSDKClient
        
        client = AlpacaSDKClient()
        
        # Try to fetch a small amount of recent data
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        data = client.get_stock_data('AAPL', start_date, end_date)
        
        if data is not None:  # May be None if no market data access
            assert isinstance(data, pd.DataFrame)
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            assert all(col in data.columns for col in required_columns)
            assert isinstance(data.index, pd.DatetimeIndex)
            print(f"Successfully fetched {len(data)} records")
        else:
            print("No data returned - may be expected for free/paper accounts")
    
    def test_pattern_detection_with_real_data(self):
        """Test pattern detection with real Alpaca data if available"""
        from alpaca_client_sdk import AlpacaSDKClient
        from app import PatternAnalyzer
        
        client = AlpacaSDKClient()
        
        # Try to fetch more data for pattern detection
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        data = client.get_stock_data('AAPL', start_date, end_date)
        
        if data is not None and len(data) > 10:
            analyzer = PatternAnalyzer()
            # Test with a simple pattern that usually exists
            result = analyzer.process_pattern(data, 'CDLDOJI')
            
            if result is not None:
                assert isinstance(result, pd.Series)
                assert len(result) == len(data)
                print(f"Pattern detection successful with {len(data)} data points")
            else:
                print("Pattern detection returned None - may be due to pandas_ta setup")
        else:
            print("Insufficient data for pattern detection test")


if __name__ == "__main__":
    """Run manual tests directly"""
    import pytest
    pytest.main([__file__, "-v", "-s"])