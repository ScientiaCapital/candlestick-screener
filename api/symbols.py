"""
API endpoint for getting stock symbols - Secured
"""
import json
import os
import csv
import logging

logger = logging.getLogger(__name__)

def load_symbols():
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
        'QQQ': {'company': 'Invesco QQQ Trust'},
        'VTI': {'company': 'Vanguard Total Stock Market ETF'},
        'IWM': {'company': 'iShares Russell 2000 ETF'},
        'GLD': {'company': 'SPDR Gold Shares'},
        'TLT': {'company': 'iShares 20+ Year Treasury Bond ETF'},
        'XLE': {'company': 'Energy Select Sector SPDR Fund'}
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

def handler(request):
    """
    Vercel serverless function handler for symbols endpoint
    Returns list of available stock symbols and companies
    """
    if request.method == 'GET':
        try:
            symbols = load_symbols()
            
            # Convert to list format for easier frontend consumption
            symbols_list = [
                {
                    'symbol': symbol,
                    'company': data.get('company', ''),
                }
                for symbol, data in symbols.items()
            ]
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({
                    'status': 'success',
                    'data': {
                        'symbols': symbols_list,
                        'count': len(symbols_list)
                    }
                })
            }
            
        except Exception as e:
            logger.error(f"Error in symbols endpoint: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'message': 'Internal server error'
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