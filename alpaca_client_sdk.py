"""
Alpaca SDK client for fetching stock market data using official alpaca-py SDK

This module provides a clean interface to the Alpaca API using the official alpaca-py SDK.
It returns data in a format compatible with yfinance for seamless integration with
existing candlestick pattern detection systems.

Classes:
    AlpacaSDKClient: Main client for fetching stock data from Alpaca API

Functions:
    get_alpaca_client: Factory function returning singleton client instance
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import time

# Official alpaca-py SDK imports
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional - environment variables can be set directly
    pass

logger = logging.getLogger(__name__)


class AlpacaSDKClient:
    """
    Client for fetching stock data from Alpaca API using official SDK.
    
    This client provides a clean interface to the Alpaca API that returns
    data in yfinance-compatible format for seamless integration with existing
    pattern detection systems.
    
    Attributes:
        api_key (str): Alpaca API key from environment variables
        secret_key (str): Alpaca secret key from environment variables
        client (StockHistoricalDataClient): Official Alpaca SDK client instance
    
    Raises:
        ValueError: If API credentials are not configured in environment variables
    """
    
    def __init__(self) -> None:
        """
        Initialize the Alpaca SDK client.
        
        Reads API credentials from environment variables ALPACA_API_KEY and
        ALPACA_SECRET_KEY, then initializes the official SDK client.
        
        Raises:
            ValueError: If required environment variables are not set
        """
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        # Validate credentials
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not configured")
        
        # Initialize the official SDK client
        self.client = StockHistoricalDataClient(self.api_key, self.secret_key)
        
        logger.info("Alpaca SDK client initialized successfully")
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format"""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Basic validation: alphanumeric, 1-5 characters, uppercase
        symbol = symbol.strip().upper()
        if len(symbol) < 1 or len(symbol) > 5:
            return False
            
        return symbol.isalnum()
    
    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Fetch stock data from Alpaca API using official SDK
        
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
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Create request using official SDK
            request_params = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Day,
                start=datetime.strptime(start_date, '%Y-%m-%d'),
                end=datetime.strptime(end_date, '%Y-%m-%d')
            )
            
            logger.debug(f"Fetching data for {symbol} from {start_date} to {end_date}")
            
            # Make API request using official SDK
            bars = self.client.get_stock_bars(request_params)
            
            if not bars.data or symbol not in bars.data:
                logger.warning(f"No bars data returned for symbol: {symbol}")
                return None
            
            # Convert to DataFrame compatible with yfinance format
            df = self._convert_to_yfinance_format(bars.data[symbol])
            
            if df is None or df.empty:
                logger.warning(f"Empty dataset for symbol: {symbol}")
                return None
                
            logger.info(f"Successfully fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def _convert_to_yfinance_format(self, bars: List) -> Optional[pd.DataFrame]:
        """
        Convert Alpaca bars to yfinance-compatible DataFrame format
        
        Args:
            bars: Bars from Alpaca SDK
            
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
                    'timestamp': bar.timestamp,
                    'Open': float(bar.open),
                    'High': float(bar.high),
                    'Low': float(bar.low),
                    'Close': float(bar.close),
                    'Volume': int(bar.volume) if bar.volume else 0
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
                logger.info("Alpaca SDK connection test successful")
                return True
            else:
                logger.error("Alpaca SDK connection test failed: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"Alpaca SDK connection test failed: {str(e)}")
            return False


# Global client instance
_alpaca_client = None


def get_alpaca_client() -> AlpacaSDKClient:
    """Get or create the global Alpaca SDK client instance"""
    global _alpaca_client
    
    if _alpaca_client is None:
        _alpaca_client = AlpacaSDKClient()
    
    return _alpaca_client