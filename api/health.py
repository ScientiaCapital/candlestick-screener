"""
API endpoint for health checks
"""
import json
import logging
from datetime import datetime
from alpaca_client_sdk import get_alpaca_client

logger = logging.getLogger(__name__)

def load_symbols():
    """Load symbols for health check"""
    import os
    import csv
    
    default_symbols = {
        'AAPL': {'company': 'Apple Inc.'},
        'GOOGL': {'company': 'Alphabet Inc.'},
        'MSFT': {'company': 'Microsoft Corporation'}
    }
    
    try:
        symbols_file = 'datasets/symbols.csv'
        if not os.path.exists(symbols_file):
            return default_symbols
            
        stocks = {}
        with open(symbols_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    symbol = row[0].strip().upper()
                    company = row[1].strip()
                    stocks[symbol] = {'company': company}
                    
        return stocks if stocks else default_symbols
        
    except Exception:
        return default_symbols

def test_alpaca_connection():
    """Test Alpaca API connection"""
    try:
        client = get_alpaca_client()
        return client.test_connection()
    except Exception as e:
        logger.error(f"Error testing Alpaca connection: {str(e)}")
        return False

def handler(request):
    """
    Vercel serverless function handler for health check
    Returns system health status
    """
    if request.method == 'GET':
        try:
            # Check if symbols are available
            symbols = load_symbols()
            symbols_status = 'ok' if symbols else 'error'
            
            # Check Alpaca API connection
            alpaca_status = 'ok'
            try:
                if test_alpaca_connection():
                    alpaca_status = 'ok'
                else:
                    alpaca_status = 'error'
            except Exception:
                alpaca_status = 'error'
            
            # Check patterns import
            patterns_status = 'ok'
            try:
                from patterns import candlestick_patterns
                patterns_status = 'ok' if candlestick_patterns else 'error'
            except Exception:
                patterns_status = 'error'
            
            # Determine overall status
            all_ok = symbols_status == 'ok' and alpaca_status == 'ok' and patterns_status == 'ok'
            overall_status = 'healthy' if all_ok else 'degraded'
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({
                    'status': overall_status,
                    'checks': {
                        'symbols': symbols_status,
                        'alpaca_api': alpaca_status,
                        'patterns': patterns_status
                    },
                    'metadata': {
                        'symbols_count': len(symbols),
                        'timestamp': datetime.now().isoformat(),
                        'version': '2.0.0-react'
                    }
                })
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            }
    
    elif request.method == 'OPTIONS':
        # Handle CORS preflight
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    else:
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'message': 'Method not allowed'
            })
        }