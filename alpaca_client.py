"""
Alpaca API client for fetching stock market data
Uses REST API directly to avoid dependency conflicts
"""

import os
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import time
from functools import wraps

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional - environment variables can be set directly
    pass

logger = logging.getLogger(__name__)

class AlpacaAPIError(Exception):
    """Custom exception for Alpaca API errors"""
    pass

class AlpacaConfig:
    """Configuration for Alpaca API"""
    
    # Paper trading credentials (as specified in requirements)
    API_KEY = os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
    # Use data endpoint for market data
    BASE_URL = os.getenv('ALPACA_DATA_URL', 'https://data.alpaca.markets')
    TRADING_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets/v2')
    
    # Rate limiting settings
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    RATE_LIMIT_DELAY = 0.1  # seconds between requests
    
    # Data settings
    MAX_DAYS_HISTORY = 365
    TIMEOUT = 30  # seconds

def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry API calls on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    last_exception = e
                    if e.response.status_code == 429:  # Rate limit
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit on attempt {attempt + 1}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    elif attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"HTTP error {e.response.status_code} on attempt {attempt + 1}: {str(e)}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"HTTP error after {max_retries} attempts: {str(e)}")
                except Exception as e:
                    last_exception = e
                    logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    
            # If all retries failed, raise the last exception
            raise last_exception
            
        return wrapper
    return decorator

class AlpacaDataClient:
    """Client for fetching stock data from Alpaca API using REST"""
    
    def __init__(self):
        """Initialize the Alpaca data client"""
        self.api_key = AlpacaConfig.API_KEY
        self.secret_key = AlpacaConfig.SECRET_KEY
        self.base_url = AlpacaConfig.BASE_URL
        
        # Validate credentials
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not configured")
        
        # Set up session
        self.session = requests.Session()
        self.session.headers.update({
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key,
            'Content-Type': 'application/json'
        })
        
        logger.info("Alpaca data client initialized successfully")
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format"""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Basic validation: alphanumeric, 1-5 characters, uppercase
        symbol = symbol.strip().upper()
        if len(symbol) < 1 or len(symbol) > 5:
            return False
            
        return symbol.isalnum()
    
    @retry_on_error(max_retries=AlpacaConfig.MAX_RETRIES, delay=AlpacaConfig.RETRY_DELAY)
    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Fetch stock data from Alpaca API
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            DataFrame with OHLCV data compatible with yfinance format
        """
        if not self.validate_symbol(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            return None
        
        symbol = symbol.upper().strip()
        
        # Set default dates if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=AlpacaConfig.MAX_DAYS_HISTORY)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Rate limiting
            time.sleep(AlpacaConfig.RATE_LIMIT_DELAY)
            
            # Build API URL - use data endpoint, not trading endpoint
            url = f"{self.base_url}/v2/stocks/{symbol}/bars"
            
            params = {
                'timeframe': '1Day',
                'start': start_date,
                'end': end_date,
                'limit': 10000,
                'adjustment': 'raw'
            }
            
            logger.debug(f"Fetching data for {symbol} from {start_date} to {end_date}")
            
            # Make API request
            response = self.session.get(url, params=params, timeout=AlpacaConfig.TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we have bars data
            if 'bars' not in data or not data['bars']:
                logger.warning(f"No bars data returned for symbol: {symbol}")
                return None
            
            # Convert to DataFrame compatible with yfinance format
            df = self._convert_to_yfinance_format(data['bars'])
            
            if df is None or df.empty:
                logger.warning(f"Empty dataset for symbol: {symbol}")
                return None
                
            logger.info(f"Successfully fetched {len(df)} records for {symbol}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {symbol}: {str(e)}")
            return None
    
    def _convert_to_yfinance_format(self, bars: List[Dict]) -> Optional[pd.DataFrame]:
        """
        Convert Alpaca bars to yfinance-compatible DataFrame format
        
        Args:
            bars: List of bar dictionaries from Alpaca API
            
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        try:
            if not bars:
                return None
            
            # Extract data from bars
            data = []
            for bar in bars:
                data.append({
                    'timestamp': bar['t'],
                    'Open': float(bar['o']),
                    'High': float(bar['h']),
                    'Low': float(bar['l']),
                    'Close': float(bar['c']),
                    'Volume': int(bar['v']) if bar['v'] else 0
                })
            
            if not data:
                return None
            
            # Create DataFrame
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Sort by date
            df = df.sort_index()
            
            # Ensure all required columns are present and properly typed
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    return None
                
                # Ensure numeric types
                if col == 'Volume':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            if df.empty:
                logger.warning("DataFrame is empty after cleaning")
                return None
            
            logger.debug(f"Converted {len(df)} bars to yfinance format")
            return df
            
        except Exception as e:
            logger.error(f"Error converting bars to DataFrame: {str(e)}")
            return None
    
    def get_multiple_stocks_data(self, symbols: list, start_date: Optional[str] = None, 
                               end_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks
        
        Args:
            symbols: List of stock symbols
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_stock_data(symbol, start_date, end_date)
                if data is not None:
                    results[symbol] = data
                else:
                    logger.warning(f"No data available for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")
                continue
        
        logger.info(f"Successfully fetched data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def test_connection(self) -> bool:
        """
        Test the connection to Alpaca API
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to fetch a small amount of data for a popular stock
            test_data = self.get_stock_data('AAPL', 
                                          start_date=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                                          end_date=datetime.now().strftime('%Y-%m-%d'))
            
            if test_data is not None and not test_data.empty:
                logger.info("Alpaca API connection test successful")
                return True
            else:
                logger.error("Alpaca API connection test failed: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"Alpaca API connection test failed: {str(e)}")
            return False
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Get basic account information to verify API access
        
        Returns:
            Account information dict or None if error
        """
        try:
            # Use trading API endpoint for account info
            trading_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
            url = f"{trading_url}/v2/account"
            response = self.session.get(url, timeout=AlpacaConfig.TIMEOUT)
            response.raise_for_status()
            
            account_data = response.json()
            logger.info("Successfully retrieved account information")
            return account_data
            
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None

# Global client instance
_alpaca_client = None

def get_alpaca_client() -> AlpacaDataClient:
    """Get or create the global Alpaca client instance"""
    global _alpaca_client
    
    if _alpaca_client is None:
        _alpaca_client = AlpacaDataClient()
    
    return _alpaca_client

# Convenience function for backward compatibility
def download(symbol: str, start: str = None, end: str = None, **kwargs) -> Optional[pd.DataFrame]:
    """
    Convenience function that mimics yfinance.download() interface
    
    Args:
        symbol: Stock symbol
        start: Start date
        end: End date
        **kwargs: Additional arguments (ignored for compatibility)
        
    Returns:
        DataFrame with stock data
    """
    client = get_alpaca_client()
    return client.get_stock_data(symbol, start, end)

def require_alpaca_auth(func):
    """Decorator to require Alpaca authentication for endpoints"""
    from functools import wraps
    from flask import jsonify
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            client = get_alpaca_client()
            # Test if client is properly configured
            if not client.api_key or not client.secret_key:
                return jsonify({'error': 'Alpaca API not configured'}), 503
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Alpaca authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    return wrapper