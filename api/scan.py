"""
API endpoint for pattern scanning - Secured version
"""
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import os
import csv
import re
import time
import hashlib

# Import business logic modules
from patterns import candlestick_patterns
from alpaca_client_sdk import get_alpaca_client

logger = logging.getLogger(__name__)

# Security constants
MAX_SYMBOLS_LIMIT = 50  # Maximum symbols to process per request
MAX_REQUEST_SIZE = 1024  # Maximum request body size in bytes
REQUEST_TIMEOUT = 30  # Request timeout in seconds

# Rate limiting storage (simple in-memory for serverless)
REQUEST_CACHE = {}
RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_REQUESTS_PER_WINDOW = 10

class StockDataManager:
    """Manages stock data operations"""
    
    def __init__(self):
        self._cache = {}
        self._alpaca_client = get_alpaca_client()
        self._use_alpaca = True
        self._use_yfinance_fallback = True

    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format"""
        import re
        SYMBOL_PATTERN = re.compile(r'^[A-Z0-9]{1,8}$')
        if not symbol or not isinstance(symbol, str):
            return False
        symbol = symbol.strip().upper()
        return bool(SYMBOL_PATTERN.match(symbol))

    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Fetch stock data with error handling"""
        if not self.validate_symbol(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            return None
            
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Try Alpaca API first
        if self._use_alpaca:
            try:
                logger.debug(f"Fetching data for {symbol} from Alpaca API")
                data = self._alpaca_client.get_stock_data(symbol, start_date, end_date)
                if data is not None and not data.empty:
                    logger.info(f"Successfully fetched {len(data)} records for {symbol} from Alpaca")
                    return data
                else:
                    logger.warning(f"No data returned from Alpaca for symbol: {symbol}")
            except Exception as e:
                logger.error(f"Error fetching data from Alpaca for {symbol}: {str(e)}")
        
        # Fallback to yfinance if available
        if self._use_yfinance_fallback:
            try:
                import yfinance as yf
                logger.debug(f"Falling back to yfinance for {symbol}")
                data = yf.download(symbol, start=start_date, end=end_date, progress=False)
                if data is not None and not data.empty:
                    logger.info(f"Successfully fetched {len(data)} records for {symbol} from yfinance fallback")
                    return data
                else:
                    logger.warning(f"No data returned from yfinance for symbol: {symbol}")
            except Exception as e:
                logger.error(f"Error downloading data from yfinance for {symbol}: {str(e)}")
        
        logger.error(f"Failed to fetch data for {symbol} from all sources")
        return None

class PatternAnalyzer:
    """Analyzes stock patterns"""
    
    @staticmethod
    def process_pattern(df: pd.DataFrame, pattern: str) -> Optional[pd.Series]:
        """Process a single pattern"""
        try:
            # Import pandas_ta here to avoid import at module level
            import pandas_ta as ta
            
            # Convert pattern name to pandas-ta format (e.g., CDLDOJI -> cdl_doji)
            pattern_name = pattern.replace('CDL', 'cdl_').lower()
            
            # Get the pattern function from pandas-ta
            pattern_func = getattr(ta, pattern_name, None)
            if pattern_func:
                result = pattern_func(df['Open'], df['High'], df['Low'], df['Close'])
                # If TA-Lib is not installed, pandas_ta returns None
                if result is None:
                    logger.warning(f"Pattern detection requires TA-Lib installation: {pattern}")
                    # Return a Series of zeros as fallback
                    return pd.Series([0] * len(df), index=df.index)
                return result
            else:
                logger.warning(f"Pattern function not found: {pattern_name}")
                # Return a Series of zeros as fallback
                return pd.Series([0] * len(df), index=df.index)
        except Exception as e:
            logger.error(f"Error processing pattern {pattern}: {str(e)}")
            # Return a Series of zeros as fallback
            return pd.Series([0] * len(df), index=df.index)

    @staticmethod
    def batch_process_patterns(df: pd.DataFrame, patterns: List[str]) -> Dict[str, pd.Series]:
        """Process multiple patterns in batch"""
        results = {}
        
        # Check for minimum data requirements
        if len(df) < 5:
            logger.warning(f"Insufficient data for pattern analysis: {len(df)} candles (minimum 5 required)")
            return results
            
        for pattern in patterns:
            result = PatternAnalyzer.process_pattern(df, pattern)
            if result is not None:
                results[pattern] = result
        return results

    @staticmethod
    def get_pattern_signal(result: float) -> Optional[str]:
        """Get pattern signal based on result value"""
        if result > 0:
            return 'bullish'
        elif result < 0:
            return 'bearish'
        return None

def load_symbols() -> Dict[str, Dict[str, str]]:
    """Load stock symbols from CSV file with fallback"""
    stocks = {}
    
    # Default symbols if file is not available
    default_symbols = {
        'AAPL': {'company': 'Apple Inc.'},
        'GOOGL': {'company': 'Alphabet Inc.'},
        'MSFT': {'company': 'Microsoft Corporation'},
        'AMZN': {'company': 'Amazon.com Inc.'},
        'TSLA': {'company': 'Tesla Inc.'},
        'META': {'company': 'Meta Platforms Inc.'},
        'NVDA': {'company': 'NVIDIA Corporation'},
        'NFLX': {'company': 'Netflix Inc.'},
        'SPY': {'company': 'SPDR S&P 500 ETF'},
        'QQQ': {'company': 'Invesco QQQ Trust'}
    }
    
    try:
        symbols_file = 'datasets/symbols.csv'
        if not os.path.exists(symbols_file):
            logger.warning(f"Symbols file not found: {symbols_file} - using default symbols")
            return default_symbols
            
        with open(symbols_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        symbol = row[0].strip().upper()
                        company = row[1].strip()
                        stocks[symbol] = {'company': company}
                except Exception as e:
                    logger.warning(f"Error processing row {row_num} in symbols file: {str(e)}")
                    continue
                    
        logger.info(f"Loaded {len(stocks)} symbols from file")
        return stocks if stocks else default_symbols
        
    except Exception as e:
        logger.warning(f"Error loading symbols file: {str(e)} - using default symbols")
        return default_symbols

def validate_request_size(request) -> bool:
    """Validate request size to prevent DoS attacks"""
    if hasattr(request, 'body') and request.body:
        if len(request.body) > MAX_REQUEST_SIZE:
            return False
    return True

def check_rate_limit(client_ip: str) -> bool:
    """Simple rate limiting for serverless environment"""
    current_time = time.time()
    
    # Clean old entries
    for ip in list(REQUEST_CACHE.keys()):
        REQUEST_CACHE[ip] = [req_time for req_time in REQUEST_CACHE[ip] 
                            if current_time - req_time < RATE_LIMIT_WINDOW]
        if not REQUEST_CACHE[ip]:
            del REQUEST_CACHE[ip]
    
    # Check current IP
    if client_ip not in REQUEST_CACHE:
        REQUEST_CACHE[client_ip] = []
    
    if len(REQUEST_CACHE[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        return False
    
    REQUEST_CACHE[client_ip].append(current_time)
    return True

def get_security_headers():
    """Get security headers for API responses"""
    return {
        'Content-Type': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Access-Control-Allow-Origin': '*',  # Will be restricted in production
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-Requested-With'
    }

def sanitize_string(input_str: str, max_length: int = 100) -> str:
    """Sanitize string input to prevent XSS"""
    if not isinstance(input_str, str):
        return ""
    
    # Remove HTML tags and escape special characters
    import html
    sanitized = html.escape(input_str.strip())
    
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def handler(request):
    """
    Vercel serverless function handler for pattern scanning - Secured
    """
    # Get client IP for rate limiting
    client_ip = getattr(request, 'remote_addr', 'unknown')
    
    # Security checks
    if not validate_request_size(request):
        return {
            'statusCode': 413,
            'headers': get_security_headers(),
            'body': json.dumps({
                'status': 'error',
                'message': 'Request entity too large'
            })
        }
    
    if not check_rate_limit(client_ip):
        return {
            'statusCode': 429,
            'headers': get_security_headers(),
            'body': json.dumps({
                'status': 'error',
                'message': 'Rate limit exceeded. Please try again later.'
            })
        }
    
    if request.method == 'OPTIONS':
        # Handle CORS preflight with security headers
        return {
            'statusCode': 200,
            'headers': get_security_headers(),
            'body': ''
        }
    
    if request.method not in ['GET', 'POST']:
        return {
            'statusCode': 405,
            'headers': get_security_headers(),
            'body': json.dumps({
                'status': 'error',
                'message': 'Method not allowed'
            })
        }
    
    try:
        # Get pattern from query params or request body with validation
        if request.method == 'GET':
            pattern = sanitize_string(request.args.get('pattern', '').strip(), 20)
            try:
                symbols_limit = min(int(request.args.get('limit', 10)), MAX_SYMBOLS_LIMIT)
            except (ValueError, TypeError):
                symbols_limit = 10
        else:  # POST
            try:
                body = json.loads(request.body or '{}')
                pattern = sanitize_string(str(body.get('pattern', '')).strip(), 20)
                symbols_limit = min(int(body.get('limit', 10)), MAX_SYMBOLS_LIMIT)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                return {
                    'statusCode': 400,
                    'headers': get_security_headers(),
                    'body': json.dumps({
                        'status': 'error',
                        'message': 'Invalid request format'
                    })
                }
        
        # Validate pattern with enhanced security
        if not pattern:
            return {
                'statusCode': 400,
                'headers': get_security_headers(),
                'body': json.dumps({
                    'status': 'error',
                    'message': 'Pattern parameter is required'
                })
            }
        
        # Additional pattern validation
        if len(pattern) > 20 or not re.match(r'^[A-Z0-9_]+$', pattern):
            return {
                'statusCode': 400,
                'headers': get_security_headers(),
                'body': json.dumps({
                    'status': 'error',
                    'message': 'Invalid pattern format'
                })
            }
        
        if pattern not in candlestick_patterns:
            return {
                'statusCode': 400,
                'headers': get_security_headers(),
                'body': json.dumps({
                    'status': 'error',
                    'message': 'Invalid pattern specified'
                })
            }
        
        # Initialize managers
        stock_manager = StockDataManager()
        pattern_analyzer = PatternAnalyzer()
        
        # Load symbols
        stocks = load_symbols()
        
        # Scan for pattern
        results = []
        processed_count = 0
        
        for symbol in list(stocks.keys())[:symbols_limit]:
            try:
                # Get stock data
                df = stock_manager.get_stock_data(symbol)
                
                if df is None or df.empty:
                    continue
                
                # Validate dataframe structure
                required_columns = ['Open', 'High', 'Low', 'Close']
                if not all(col in df.columns for col in required_columns):
                    logger.warning(f"Invalid data format for {symbol}")
                    continue
                    
                if len(df) < 5:  # Need minimum data for pattern analysis
                    continue
                    
                # Process pattern
                pattern_results = pattern_analyzer.batch_process_patterns(df, [pattern])
                if pattern in pattern_results and not pattern_results[pattern].empty:
                    last_value = pattern_results[pattern].iloc[-1]
                    signal = pattern_analyzer.get_pattern_signal(last_value)
                    
                    if signal:  # Only include symbols with actual signals
                        results.append({
                            'symbol': sanitize_string(symbol, 10),
                            'company': sanitize_string(stocks[symbol].get('company', ''), 100),
                            'signal': sanitize_string(signal, 10),
                            'value': round(float(last_value), 4),  # Limit precision
                            'date': df.index[-1].strftime('%Y-%m-%d') if hasattr(df.index[-1], 'strftime') else str(df.index[-1])[:10]
                        })
                        processed_count += 1
                        
            except Exception as e:
                logger.error(f'Failed to process {symbol}: {str(e)}')
                continue
        
        return {
            'statusCode': 200,
            'headers': get_security_headers(),
            'body': json.dumps({
                'status': 'success',
                'data': {
                    'pattern': sanitize_string(pattern, 20),
                    'pattern_name': sanitize_string(candlestick_patterns.get(pattern, ''), 100),
                    'results': results,
                    'processed_count': processed_count,
                    'total_symbols': min(len(stocks), 1000),  # Limit exposure
                    'request_timestamp': datetime.now().isoformat()[:19]  # No microseconds
                }
            })
        }
        
    except Exception as e:
        # Log error but don't expose details to client
        logger.error(f"Error in scan endpoint: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_security_headers(),
            'body': json.dumps({
                'status': 'error',
                'message': 'Internal server error',
                'error_id': hashlib.md5(str(e).encode()).hexdigest()[:8]  # Safe error reference
            })
        }