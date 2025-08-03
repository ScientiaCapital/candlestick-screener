import os
import csv
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import BadRequest, InternalServerError
import yfinance as yf
import logging
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv

from patterns import candlestick_patterns

from config import Config
from cache_manager import (
    cache_stock_data, cache_pattern_analysis, cache_symbol_list,
    invalidate_cache, get_cache_stats, cache
)
from rate_limiter import (
    limit_snapshot, limit_pattern_analysis, limit_index,
    limit_burst, get_rate_limit_stats, init_app as init_rate_limiter
)
from security import (
    init_security, InputValidator, SecurityMiddleware, 
    CSRFProtection, validate_request_data
)
from alpaca_client_sdk import get_alpaca_client
from alpaca_client import AlpacaAPIError, require_alpaca_auth

# Configure logging - optimized for serverless
log_handlers = [logging.StreamHandler()]

# Only add file handler in development or when persistent storage is available
if os.getenv('FLASK_ENV') != 'production' and os.access(os.getcwd(), os.W_OK):
    try:
        log_handlers.append(logging.FileHandler('app.log'))
    except (PermissionError, OSError):
        pass  # Skip file logging if not possible

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate configuration
config_issues = Config.validate()
if config_issues:
    logger.warning("Configuration issues found: %s", config_issues)
    if Config.FLASK_ENV == 'production' and config_issues:
        logger.error("Production configuration errors detected. Exiting...")
        raise SystemExit("Production configuration incomplete")

class StockDataManager:
    """Manages stock data operations"""
    
    def __init__(self):
        self._cache = {}
        self._alpaca_client = get_alpaca_client()
        self._use_alpaca = True  # Primary data source
        self._use_yfinance_fallback = True  # Fallback option

    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format using security validator"""
        return InputValidator.validate_symbol(symbol)

    @cache_stock_data()
    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Fetch stock data with error handling and caching"""
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
        
        # Fallback to yfinance if Alpaca fails
        if self._use_yfinance_fallback:
            try:
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

    def test_alpaca_connection(self) -> bool:
        """Test Alpaca API connection"""
        try:
            return self._alpaca_client.test_connection()
        except Exception as e:
            logger.error(f"Error testing Alpaca connection: {str(e)}")
            return False

    def save_stock_data(self, symbol: str, data: pd.DataFrame) -> bool:
        """Save stock data to CSV file - serverless optimized"""
        try:
            # Check if we have write access (not available in serverless)
            if not os.access(os.getcwd(), os.W_OK):
                logger.warning(f"No write access - caching {symbol} data in memory only")
                # Invalidate cache for this symbol but don't save to disk
                invalidate_cache('stock_data', symbol)
                return True
            
            # Ensure directory exists
            os.makedirs('datasets/daily', exist_ok=True)
            # Save with index (dates)
            data.to_csv(f'datasets/daily/{symbol}.csv')
            # Invalidate cache for this symbol
            invalidate_cache('stock_data', symbol)
            logger.info(f"Successfully saved data for {symbol}")
            return True
        except Exception as e:
            logger.warning(f"Could not save data for {symbol} to disk: {str(e)} - using cache only")
            # Still invalidate cache to refresh in-memory data
            invalidate_cache('stock_data', symbol)
            return True  # Return True since we can still function without disk storage

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
    @cache_pattern_analysis()
    def batch_process_patterns(df: pd.DataFrame, patterns: List[str]) -> Dict[str, pd.Series]:
        """Process multiple patterns in batch with caching"""
        results = {}
        
        # Check for minimum data requirements (most patterns need at least 5 candles)
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

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
cache.init_app(app, config=Config.get_cache_config())

# Initialize rate limiter
init_rate_limiter(app)

# Initialize security
init_security(app)

# Initialize managers
stock_manager = StockDataManager()
pattern_analyzer = PatternAnalyzer()

@cache_symbol_list()
def load_symbols() -> Dict[str, Dict[str, str]]:
    """Load stock symbols from CSV file with caching - serverless optimized"""
    stocks = {}
    
    # Default symbols if file is not available (serverless fallback)
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

@app.route('/snapshot')
@limit_snapshot()
@CSRFProtection.require_csrf_token
@SecurityMiddleware.validate_request_size()
def snapshot():
    """Update stock data for all symbols - serverless optimized"""
    try:
        # Load symbols using the optimized function
        stocks_dict = load_symbols()
        symbols = list(stocks_dict.keys())
        
        if not symbols:
            return jsonify({"status": "error", "message": "No symbols available"}), 400
            
        updated_count = 0
        failed_count = 0
        
        # Process symbols in batches
        for i in range(0, len(symbols), Config.BATCH_SIZE):
            batch = symbols[i:i + Config.BATCH_SIZE]
            for symbol in batch:
                try:
                    data = stock_manager.get_stock_data(symbol)
                    if data is not None and not data.empty:
                        if stock_manager.save_stock_data(symbol, data):
                            updated_count += 1
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error processing symbol {symbol}: {str(e)}")
                    failed_count += 1
        
        return jsonify({
            "status": "success", 
            "message": f"Data update completed. Updated: {updated_count}, Failed: {failed_count}",
            "updated": updated_count,
            "failed": failed_count
        })
    except FileNotFoundError:
        logger.error("Symbols file not found")
        return jsonify({"status": "error", "message": "Symbols file not found"}), 404
    except Exception as e:
        logger.error(f"Error in snapshot: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/')
@limit_index()
@SecurityMiddleware.validate_pattern_input
def index():
    """Main page with pattern scanning functionality"""
    pattern = request.args.get('pattern', '').strip()
    
    try:
        stocks = load_symbols()
        
        if pattern:
            # Validate pattern
            if pattern not in candlestick_patterns:
                logger.warning(f"Invalid pattern requested: {pattern}")
                return render_template('index.html', 
                                    candlestick_patterns=candlestick_patterns, 
                                    stocks=stocks, 
                                    pattern='',
                                    error='Invalid pattern selected')
            
            # Serverless optimization: get data dynamically instead of reading from files
            processed_count = 0
            for symbol in list(stocks.keys())[:10]:  # Limit processing for demo
                try:
                    # Get fresh data from Alpaca API
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
                        
                    results = pattern_analyzer.batch_process_patterns(df, [pattern])
                    if pattern in results and not results[pattern].empty:
                        last_value = results[pattern].iloc[-1]
                        signal = pattern_analyzer.get_pattern_signal(last_value)
                        if signal:
                            stocks[symbol][pattern] = signal
                            processed_count += 1
                            
                except Exception as e:
                    logger.error(f'Failed to process {symbol}: {str(e)}')
                    continue
            
            logger.info(f"Processed pattern {pattern} for {processed_count} symbols")

        return render_template('index.html', 
                             candlestick_patterns=candlestick_patterns, 
                             stocks=stocks, 
                             pattern=pattern)
                             
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', 
                             candlestick_patterns=candlestick_patterns, 
                             stocks={}, 
                             pattern='',
                             error='An error occurred while loading data')

@app.route('/stats')
@limit_burst()
def stats():
    """Get system statistics"""
    try:
        return jsonify({
            'cache': get_cache_stats(),
            'rate_limits': get_rate_limit_stats(),
            'symbols_count': len(load_symbols()),
            'server_time': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Unable to fetch statistics'}), 500

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check cache connection
        cache_status = 'ok'
        try:
            get_cache_stats()
        except Exception:
            cache_status = 'error'
            
        # Check if symbols are available (either from file or defaults)
        symbols = load_symbols()
        symbols_status = 'ok' if symbols else 'error'
        
        # Check Alpaca API connection
        alpaca_status = 'ok'
        try:
            if stock_manager.test_alpaca_connection():
                alpaca_status = 'ok'
            else:
                alpaca_status = 'error'
        except Exception:
            alpaca_status = 'error'
        
        # Determine overall status
        all_ok = cache_status == 'ok' and symbols_status == 'ok' and alpaca_status == 'ok'
        overall_status = 'healthy' if all_ok else 'degraded'
        
        return jsonify({
            'status': overall_status,
            'cache': cache_status,
            'symbols': symbols_status,
            'alpaca_api': alpaca_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Alpaca API endpoints
@app.route('/api/alpaca/account')
@limit_burst()
@CSRFProtection.require_csrf_token
@SecurityMiddleware.validate_request_size()
@require_alpaca_auth
def get_alpaca_account():
    """Get Alpaca account information"""
    try:
        client = get_alpaca_client()
        account_data = client.get_account_info()
        
        # Sanitize account data before sending to frontend
        safe_account_data = {
            'status': account_data.get('status'),
            'currency': account_data.get('currency'),
            'buying_power': account_data.get('buying_power'),
            'cash': account_data.get('cash'),
            'portfolio_value': account_data.get('portfolio_value'),
            'day_trade_count': account_data.get('day_trade_count'),
            'trading_blocked': account_data.get('trading_blocked', False)
        }
        
        return jsonify({
            'status': 'success',
            'data': safe_account_data
        })
        
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error in account endpoint: {str(e)}")
        return jsonify({'error': 'API service unavailable'}), 503
    except Exception as e:
        logger.error(f"Error in alpaca account endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/alpaca/positions')
@limit_burst()
@CSRFProtection.require_csrf_token
@SecurityMiddleware.validate_request_size()
@require_alpaca_auth
def get_alpaca_positions():
    """Get Alpaca positions"""
    try:
        client = get_alpaca_client()
        # Note: positions not implemented in current alpaca_client
        positions = []
        
        # Sanitize position data
        safe_positions = []
        for position in positions:
            safe_position = {
                'symbol': position.get('symbol'),
                'qty': position.get('qty'),
                'market_value': position.get('market_value'),
                'side': position.get('side'),
                'unrealized_pl': position.get('unrealized_pl'),
                'unrealized_plpc': position.get('unrealized_plpc')
            }
            safe_positions.append(safe_position)
        
        return jsonify({
            'status': 'success',
            'data': safe_positions
        })
        
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error in positions endpoint: {str(e)}")
        return jsonify({'error': 'API service unavailable'}), 503
    except Exception as e:
        logger.error(f"Error in alpaca positions endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/alpaca/bars/<symbol>')
@limit_burst()
@SecurityMiddleware.validate_symbol_input
@SecurityMiddleware.validate_request_size()
def get_alpaca_bars(symbol):
    """Get historical bars for a symbol"""
    try:
        # Validate symbol
        if not InputValidator.validate_symbol(symbol):
            return jsonify({'error': 'Invalid symbol format'}), 400
        
        # Get optional parameters
        timeframe = request.args.get('timeframe', '1Day')
        start = request.args.get('start')
        end = request.args.get('end')
        limit = int(request.args.get('limit', 100))
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            return jsonify({'error': 'Invalid limit (1-1000)'}), 400
        
        client = get_alpaca_client()
        # Use get_stock_data method
        bars_data = client.get_stock_data(symbol, start, end)
        
        return jsonify({
            'status': 'success',
            'data': bars_data
        })
        
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error in bars endpoint: {str(e)}")
        return jsonify({'error': 'API service unavailable'}), 503
    except ValueError as e:
        logger.error(f"Invalid parameter in bars endpoint: {str(e)}")
        return jsonify({'error': 'Invalid parameters'}), 400
    except Exception as e:
        logger.error(f"Error in alpaca bars endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure required directories exist (only if writable)
    try:
        if os.access(os.getcwd(), os.W_OK):
            os.makedirs('datasets/daily', exist_ok=True)
    except (PermissionError, OSError):
        logger.info("No write access - running in serverless mode")
    
    # Validate critical configuration
    config_issues = Config.validate()
    if config_issues.get('errors') and Config.FLASK_ENV == 'production':
        logger.error(f"Production configuration errors: {config_issues['errors']}")
        raise SystemExit("Production configuration incomplete")
    
    # Log configuration warnings
    if config_issues.get('warnings'):
        logger.warning(f"Configuration warnings: {config_issues['warnings']}")
    
    # Run application
    port = int(os.getenv('PORT', 5000))
    
    # Security: Disable debug in production
    debug_mode = Config.FLASK_DEBUG and Config.FLASK_ENV != 'production'
    
    logger.info(f"Starting application on port {port} in {Config.FLASK_ENV} mode")
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0' if Config.FLASK_ENV == 'production' else '127.0.0.1',
        port=port,
        threaded=True
    )
