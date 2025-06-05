import os
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from app import app as flask_app
import pandas as pd
import numpy as np

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_DEBUG'] = 'False'
    yield
    # Cleanup after tests
    if os.path.exists('datasets/daily'):
        for file in os.listdir('datasets/daily'):
            os.remove(os.path.join('datasets/daily', file))

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app

@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()

@pytest.fixture
def mock_stock_data():
    """Create mock stock data for testing."""
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
    data = {
        'Open': np.random.uniform(100, 200, len(dates)),
        'High': np.random.uniform(200, 300, len(dates)),
        'Low': np.random.uniform(50, 100, len(dates)),
        'Close': np.random.uniform(100, 200, len(dates)),
        'Volume': np.random.uniform(1000000, 5000000, len(dates))
    }
    return pd.DataFrame(data, index=dates)

@pytest.fixture
def mock_symbols_file(tmp_path):
    """Create a temporary symbols.csv file for testing."""
    symbols_file = tmp_path / "symbols.csv"
    symbols_file.write_text("AAPL,Apple Inc.\nMSFT,Microsoft Corporation\n")
    return str(symbols_file)

@pytest.fixture
def mock_daily_data_dir(tmp_path):
    """Create a temporary directory with mock daily data files."""
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    
    # Create mock data for AAPL
    aapl_data = pd.DataFrame({
        'Open': [150, 151, 152, 153, 154],
        'High': [155, 156, 157, 158, 159],
        'Low': [145, 146, 147, 148, 149],
        'Close': [152, 153, 154, 155, 156],
        'Volume': [1000000] * 5
    })
    aapl_data.to_csv(daily_dir / "AAPL.csv")
    
    # Create mock data for MSFT
    msft_data = pd.DataFrame({
        'Open': [250, 251, 252, 253, 254],
        'High': [255, 256, 257, 258, 259],
        'Low': [245, 246, 247, 248, 249],
        'Close': [252, 253, 254, 255, 256],
        'Volume': [2000000] * 5
    })
    msft_data.to_csv(daily_dir / "MSFT.csv")
    
    return str(daily_dir)

@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    return Mock()

@pytest.fixture
def mock_cache():
    """Mock cache object"""
    return Mock()

@pytest.fixture
def mock_limiter():
    """Mock rate limiter"""
    return Mock()

@pytest.fixture
def test_env():
    """Set up test environment variables"""
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_DEBUG'] = 'True'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['ALPHA_VANTAGE_API_KEY'] = 'test-api-key'
    os.environ['CACHE_TYPE'] = 'redis'
    os.environ['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
    os.environ['CACHE_TIMEOUT'] = '300'
    os.environ['RATELIMIT_STORAGE_URL'] = 'redis://localhost:6379/0'
    os.environ['RATELIMIT_DEFAULT'] = '200/hour'
    yield
    # Clean up
    for key in [
        'FLASK_APP', 'FLASK_ENV', 'FLASK_DEBUG', 'SECRET_KEY',
        'ALPHA_VANTAGE_API_KEY', 'CACHE_TYPE', 'CACHE_REDIS_URL',
        'CACHE_TIMEOUT', 'RATELIMIT_STORAGE_URL', 'RATELIMIT_DEFAULT'
    ]:
        os.environ.pop(key, None) 