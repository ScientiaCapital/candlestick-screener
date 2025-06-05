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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
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

    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format"""
        if not symbol or not isinstance(symbol, str):
            return False
        # Check for valid symbol format (alphanumeric, max 5 chars)
        symbol = symbol.strip().upper()
        return bool(symbol.isalnum() and 1 <= len(symbol) <= 5)

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
        
        try:
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if data is None or data.empty:
                logger.warning(f"No data returned for symbol: {symbol}")
                return None
            return data
        except Exception as e:
            logger.error(f"Error downloading data for {symbol}: {str(e)}")
            return None

    def save_stock_data(self, symbol: str, data: pd.DataFrame) -> bool:
        """Save stock data to CSV file"""
        try:
            # Ensure directory exists
            os.makedirs('datasets/daily', exist_ok=True)
            # Save with index (dates)
            data.to_csv(f'datasets/daily/{symbol}.csv')
            # Invalidate cache for this symbol
            invalidate_cache('stock_data', symbol)
            logger.info(f"Successfully saved data for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error saving data for {symbol}: {str(e)}")
            return False

class PatternAnalyzer:
    """Analyzes stock patterns"""
    
    @staticmethod
    def process_pattern(df: pd.DataFrame, pattern: str) -> Optional[pd.Series]:
        """Process a single pattern"""
        try:
            # Import pandas_ta here to avoid import at module level
            import pandas_ta as ta
            
            # Add TA indicators to dataframe
            df.ta.add_all_ta_features = True
            
            # Convert pattern name to pandas-ta format
            pattern_name = pattern.replace('CDL', '').lower()
            
            # Get the pattern function from pandas-ta
            pattern_func = getattr(ta.cdl, pattern_name, None)
            if pattern_func:
                result = pattern_func(df['Open'], df['High'], df['Low'], df['Close'])
                return result
            else:
                logger.warning(f"Pattern function not found: {pattern_name}")
                return None
        except Exception as e:
            logger.error(f"Error processing pattern {pattern}: {str(e)}")
            return None

    @staticmethod
    @cache_pattern_analysis()
    def batch_process_patterns(df: pd.DataFrame, patterns: List[str]) -> Dict[str, pd.Series]:
        """Process multiple patterns in batch with caching"""
        results = {}
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

# Initialize managers
stock_manager = StockDataManager()
pattern_analyzer = PatternAnalyzer()

@cache_symbol_list()
def load_symbols() -> Dict[str, Dict[str, str]]:
    """Load stock symbols from CSV file with caching"""
    stocks = {}
    try:
        symbols_file = 'datasets/symbols.csv'
        if not os.path.exists(symbols_file):
            logger.error(f"Symbols file not found: {symbols_file}")
            return stocks
            
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
                    
        logger.info(f"Loaded {len(stocks)} symbols")
    except Exception as e:
        logger.error(f"Error loading symbols: {str(e)}")
    return stocks

@app.route('/snapshot')
@limit_snapshot()
def snapshot():
    """Update stock data for all symbols"""
    try:
        # Check if symbols file exists
        if not os.path.exists('datasets/symbols.csv'):
            logger.error("Symbols file not found")
            return jsonify({"status": "error", "message": "Symbols file not found"}), 404
            
        symbols = []
        with open('datasets/symbols.csv', 'r') as f:
            for line in f:
                if "," in line:
                    symbol = line.split(",")[0].strip()
                    if symbol:
                        symbols.append(symbol)
        
        if not symbols:
            return jsonify({"status": "error", "message": "No symbols found"}), 400
            
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
            
            # Check if daily data directory exists
            daily_dir = 'datasets/daily'
            if not os.path.exists(daily_dir):
                logger.error("Daily data directory not found")
                return render_template('index.html', 
                                    candlestick_patterns=candlestick_patterns, 
                                    stocks=stocks, 
                                    pattern='',
                                    error='Stock data not available')
            
            processed_count = 0
            for filename in os.listdir(daily_dir):
                if not filename.endswith('.csv'):
                    continue
                    
                try:
                    file_path = os.path.join(daily_dir, filename)
                    if not os.path.exists(file_path):
                        continue
                        
                    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
                    
                    # Validate dataframe structure
                    required_columns = ['Open', 'High', 'Low', 'Close']
                    if not all(col in df.columns for col in required_columns):
                        logger.warning(f"Invalid data format in {filename}")
                        continue
                        
                    if len(df) < 5:  # Need minimum data for pattern analysis
                        continue
                        
                    symbol = filename.split('.')[0]
                    if symbol in stocks:
                        results = pattern_analyzer.batch_process_patterns(df, [pattern])
                        if pattern in results and not results[pattern].empty:
                            last_value = results[pattern].iloc[-1]
                            signal = pattern_analyzer.get_pattern_signal(last_value)
                            if signal:
                                stocks[symbol][pattern] = signal
                                processed_count += 1
                except Exception as e:
                    logger.error(f'Failed to process {filename}: {str(e)}')
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
            
        # Check if symbols file exists
        symbols_status = 'ok' if os.path.exists('datasets/symbols.csv') else 'error'
        
        return jsonify({
            'status': 'healthy' if cache_status == 'ok' and symbols_status == 'ok' else 'degraded',
            'cache': cache_status,
            'symbols_file': symbols_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs('datasets/daily', exist_ok=True)
    
    # Run application
    port = int(os.getenv('PORT', 5000))
    app.run(
        debug=Config.FLASK_DEBUG,
        host='0.0.0.0' if Config.FLASK_ENV == 'production' else '127.0.0.1',
        port=port
    )
