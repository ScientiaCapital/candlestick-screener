import pytest
import os
import pandas as pd
from unittest.mock import patch, mock_open, MagicMock
from app import app, stock_manager, pattern_analyzer

def test_index_page(client):
    """Test the main index page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Technical Scanner' in response.data
    assert b'Select a Pattern' in response.data

def test_index_page_with_pattern(client, mock_daily_data_dir, mock_symbols_file):
    """Test the index page with a pattern selected."""
    with patch('app.open', mock_open(read_data='AAPL,Apple Inc.\nMSFT,Microsoft Corporation\n')):
        with patch('os.listdir', return_value=['AAPL.csv', 'MSFT.csv']):
            with patch('pandas.read_csv') as mock_read_csv:
                # Mock the CSV data
                mock_data = pd.DataFrame({
                    'Open': [150] * 5,
                    'High': [160] * 5,
                    'Low': [140] * 5,
                    'Close': [155] * 5
                })
                mock_read_csv.return_value = mock_data
                
                # Test with a pattern
                response = client.get('/?pattern=CDLENGULFING')
                assert response.status_code == 200
                assert b'Technical Scanner' in response.data
                assert b'CDLENGULFING' in response.data

def test_snapshot_endpoint(client, mock_symbols_file):
    """Test the snapshot endpoint."""
    with patch('app.open', mock_open(read_data='AAPL,Apple Inc.\nMSFT,Microsoft Corporation\n')):
        with patch('app.stock_manager.get_stock_data') as mock_get_data:
            # Mock successful data download
            mock_data = pd.DataFrame({
                'Open': [150] * 5,
                'High': [160] * 5,
                'Low': [140] * 5,
                'Close': [155] * 5,
                'Volume': [1000000] * 5
            })
            mock_get_data.return_value = mock_data
            
            # Mock os.makedirs to prevent actual directory creation
            with patch('os.makedirs', MagicMock()):
                response = client.get('/snapshot')
                assert response.status_code == 200
                assert b'success' in response.data.lower()

def test_snapshot_endpoint_error(client, mock_symbols_file):
    """Test the snapshot endpoint with an error."""
    # Mock load_symbols to return exactly 2 symbols
    test_symbols = {
        'AAPL': {'company': 'Apple Inc.'},
        'MSFT': {'company': 'Microsoft Corporation'}
    }
    with patch('app.load_symbols', return_value=test_symbols):
        with patch('app.stock_manager.get_stock_data', side_effect=Exception('Test error')):
            response = client.get('/snapshot')
            assert response.status_code == 200  # Graceful error handling
            data = response.get_json()
            assert data['status'] == 'success'
            assert data['failed'] == 2  # Both symbols should fail
            assert data['updated'] == 0  # No successful updates

def test_invalid_pattern(client):
    """Test the index page with an invalid pattern."""
    response = client.get('/?pattern=INVALIDPATTERN')
    assert response.status_code == 200
    assert b'Technical Scanner' in response.data
    # Should show error message for invalid pattern
    assert b'Invalid pattern selected' in response.data

def test_stock_manager_validation():
    """Test stock symbol validation."""
    assert stock_manager.validate_symbol('AAPL') is True
    assert stock_manager.validate_symbol('') is False
    assert stock_manager.validate_symbol('123') is True
    assert stock_manager.validate_symbol('AAPL!') is False
    assert stock_manager.validate_symbol(None) is False

def test_pattern_analyzer_signals():
    """Test pattern signal generation."""
    assert pattern_analyzer.get_pattern_signal(100) == 'bullish'
    assert pattern_analyzer.get_pattern_signal(-100) == 'bearish'
    assert pattern_analyzer.get_pattern_signal(0) is None 