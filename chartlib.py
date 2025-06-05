import os
import pandas as pd
from typing import Optional


def is_consolidating(df: pd.DataFrame, percentage: float = 2.0) -> bool:
    """
    Check if a stock is consolidating based on recent price action.
    
    Args:
        df: DataFrame with OHLC data
        percentage: Consolidation threshold percentage
        
    Returns:
        bool: True if stock is consolidating
    """
    if len(df) < 15:
        return False
        
    recent_candlesticks = df[-15:]
    
    max_close = recent_candlesticks['Close'].max()
    min_close = recent_candlesticks['Close'].min()

    threshold = 1 - (percentage / 100)
    if min_close > (max_close * threshold):
        return True        

    return False


def is_breaking_out(df: pd.DataFrame, percentage: float = 2.5) -> bool:
    """
    Check if a stock is breaking out of consolidation.
    
    Args:
        df: DataFrame with OHLC data
        percentage: Breakout threshold percentage
        
    Returns:
        bool: True if stock is breaking out
    """
    if len(df) < 16:
        return False
        
    last_close = df[-1:]['Close'].values[0]

    if is_consolidating(df[:-1], percentage=percentage):
        recent_closes = df[-16:-1]

        if last_close > recent_closes['Close'].max():
            return True

    return False


def scan_for_patterns(data_directory: str = 'datasets/daily') -> dict:
    """
    Scan all stocks in directory for consolidation and breakout patterns.
    
    Args:
        data_directory: Directory containing stock CSV files
        
    Returns:
        dict: Results with consolidating and breaking_out lists
    """
    results = {
        'consolidating': [],
        'breaking_out': [],
        'errors': []
    }
    
    if not os.path.exists(data_directory):
        results['errors'].append(f"Directory {data_directory} does not exist")
        return results
    
    for filename in os.listdir(data_directory):
        if not filename.endswith('.csv'):
            continue
            
        try:
            filepath = os.path.join(data_directory, filename)
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            # Validate required columns
            required_columns = ['Open', 'High', 'Low', 'Close']
            if not all(col in df.columns for col in required_columns):
                results['errors'].append(f"Missing required columns in {filename}")
                continue
            
            symbol = filename.replace('.csv', '')
            
            if is_consolidating(df, percentage=2.5):
                results['consolidating'].append(symbol)

            if is_breaking_out(df):
                results['breaking_out'].append(symbol)
                
        except Exception as e:
            results['errors'].append(f"Error processing {filename}: {str(e)}")
    
    return results


if __name__ == "__main__":
    """Script execution for testing purposes only"""
    results = scan_for_patterns()
    
    print(f"Consolidating stocks: {len(results['consolidating'])}")
    for symbol in results['consolidating']:
        print(f"  {symbol} is consolidating")
    
    print(f"\nBreaking out stocks: {len(results['breaking_out'])}")
    for symbol in results['breaking_out']:
        print(f"  {symbol} is breaking out")
        
    if results['errors']:
        print(f"\nErrors encountered: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  {error}")