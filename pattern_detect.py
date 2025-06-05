import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PatternDetector:
    """Advanced pattern detection using multiple technical analysis libraries"""
    
    def __init__(self):
        self.supported_patterns = [
            'CDL_MORNINGSTAR',
            'CDL_ENGULFING',
            'CDL_HAMMER',
            'CDL_DOJI',
            'CDL_SHOOTINGSTAR'
        ]
    
    def fetch_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        Fetch stock data for analysis
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            
        Returns:
            DataFrame with OHLC data or None if error
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if data.empty:
                logger.warning(f"No data found for symbol: {symbol}")
                return None
                
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def detect_pattern(self, data: pd.DataFrame, pattern_name: str) -> Optional[pd.Series]:
        """
        Detect specific candlestick pattern
        
        Args:
            data: OHLC DataFrame
            pattern_name: Name of pattern to detect
            
        Returns:
            Series with pattern signals or None if error
        """
        try:
            import pandas_ta as ta
            
            if pattern_name not in self.supported_patterns:
                logger.warning(f"Pattern {pattern_name} not supported")
                return None
            
            # Convert pattern name to pandas-ta format
            pattern_func_name = pattern_name.replace('CDL_', '').lower()
            
            # Get the pattern function
            if hasattr(ta.cdl, pattern_func_name):
                pattern_func = getattr(ta.cdl, pattern_func_name)
                result = pattern_func(data['Open'], data['High'], data['Low'], data['Close'])
                return result
            else:
                logger.error(f"Pattern function {pattern_func_name} not found")
                return None
                
        except ImportError:
            logger.error("pandas_ta library not installed. Install with: pip install pandas_ta")
            return None
        except Exception as e:
            logger.error(f"Error detecting pattern {pattern_name}: {str(e)}")
            return None
    
    def analyze_multiple_patterns(self, data: pd.DataFrame, patterns: List[str]) -> Dict[str, pd.Series]:
        """
        Analyze multiple patterns on the same data
        
        Args:
            data: OHLC DataFrame
            patterns: List of pattern names to analyze
            
        Returns:
            Dictionary mapping pattern names to their signals
        """
        results = {}
        
        for pattern in patterns:
            result = self.detect_pattern(data, pattern)
            if result is not None:
                results[pattern] = result
                
        return results
    
    def get_recent_signals(self, data: pd.DataFrame, pattern_name: str, days: int = 30) -> pd.DataFrame:
        """
        Get recent pattern signals
        
        Args:
            data: OHLC DataFrame with pattern signals
            pattern_name: Pattern column name
            days: Number of recent days to check
            
        Returns:
            DataFrame with recent signals
        """
        if pattern_name not in data.columns:
            logger.warning(f"Pattern {pattern_name} not found in data")
            return pd.DataFrame()
        
        # Get recent data
        recent_data = data.tail(days)
        
        # Filter non-zero signals
        signals = recent_data[recent_data[pattern_name] != 0]
        
        return signals
    
    def analyze_symbol(self, symbol: str, patterns: List[str] = None) -> Dict:
        """
        Complete analysis of a symbol for specified patterns
        
        Args:
            symbol: Stock symbol to analyze
            patterns: List of patterns to check (default: all supported)
            
        Returns:
            Dictionary with analysis results
        """
        if patterns is None:
            patterns = self.supported_patterns
            
        results = {
            'symbol': symbol,
            'patterns': {},
            'recent_signals': {},
            'errors': []
        }
        
        # Fetch data
        data = self.fetch_stock_data(symbol)
        if data is None:
            results['errors'].append(f"Failed to fetch data for {symbol}")
            return results
        
        # Analyze patterns
        pattern_results = self.analyze_multiple_patterns(data, patterns)
        
        for pattern_name, signals in pattern_results.items():
            results['patterns'][pattern_name] = {
                'total_signals': (signals != 0).sum(),
                'bullish_signals': (signals > 0).sum(),
                'bearish_signals': (signals < 0).sum(),
                'latest_signal': signals.iloc[-1] if len(signals) > 0 else 0
            }
            
            # Add pattern column to data for recent signals analysis
            data[pattern_name] = signals
            
            # Get recent signals
            recent = self.get_recent_signals(data, pattern_name, days=30)
            if not recent.empty:
                results['recent_signals'][pattern_name] = recent.index.strftime('%Y-%m-%d').tolist()
        
        return results


def example_analysis():
    """Example usage of the PatternDetector class"""
    detector = PatternDetector()
    
    # Analyze SPY for common patterns
    patterns_to_check = ['CDL_MORNINGSTAR', 'CDL_ENGULFING']
    results = detector.analyze_symbol('SPY', patterns_to_check)
    
    print(f"Analysis for {results['symbol']}:")
    for pattern, stats in results['patterns'].items():
        print(f"\n{pattern}:")
        print(f"  Total signals: {stats['total_signals']}")
        print(f"  Bullish: {stats['bullish_signals']}")
        print(f"  Bearish: {stats['bearish_signals']}")
        print(f"  Latest signal: {stats['latest_signal']}")
        
        if pattern in results['recent_signals']:
            print(f"  Recent signal dates: {results['recent_signals'][pattern]}")
    
    if results['errors']:
        print(f"\nErrors: {results['errors']}")


if __name__ == "__main__":
    """Run example analysis when script is executed directly"""
    example_analysis()