"""
API endpoint for getting available candlestick patterns - Secured
"""
import json
from patterns import candlestick_patterns
import time
import hashlib

# Simple rate limiting
REQUEST_CACHE = {}
RATE_LIMIT_WINDOW = 60  # 1 minute
MAX_REQUESTS_PER_WINDOW = 20

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
        'Cache-Control': 'public, max-age=3600',  # Cache patterns for 1 hour
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

def handler(request):
    """
    Vercel serverless function handler for patterns endpoint - Secured
    Returns list of available candlestick patterns
    """
    # Rate limiting
    client_ip = getattr(request, 'remote_addr', 'unknown')
    if not check_rate_limit(client_ip):
        return {
            'statusCode': 429,
            'headers': get_security_headers(),
            'body': json.dumps({
                'status': 'error',
                'message': 'Rate limit exceeded. Please try again later.'
            })
        }
    
    if request.method == 'GET':
        try:
            return {
                'statusCode': 200,
                'headers': get_security_headers(),
                'body': json.dumps({
                    'status': 'success',
                    'data': {
                        'patterns': candlestick_patterns,
                        'count': len(candlestick_patterns)
                    }
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': get_security_headers(),
                'body': json.dumps({
                    'status': 'error',
                    'message': 'Internal server error',
                    'error_id': hashlib.md5(str(e).encode()).hexdigest()[:8]
                })
            }
    
    elif request.method == 'OPTIONS':
        # Handle CORS preflight
        return {
            'statusCode': 200,
            'headers': get_security_headers(),
            'body': ''
        }
    
    else:
        return {
            'statusCode': 405,
            'headers': get_security_headers(),
            'body': json.dumps({
                'status': 'error',
                'message': 'Method not allowed'
            })
        }