"""
Security utilities and enhancements for the candlestick screener application
"""
import re
import html
from functools import wraps
from typing import Optional, List, Dict, Any
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """Input validation utilities"""
    
    # Regex patterns for validation
    SYMBOL_PATTERN = re.compile(r'^[A-Z0-9]{1,5}$')
    PATTERN_NAME_PATTERN = re.compile(r'^CDL[A-Z0-9]+$')
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> bool:
        """
        Validate stock symbol format
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            bool: True if valid
        """
        if not symbol or not isinstance(symbol, str):
            return False
        
        symbol = symbol.strip().upper()
        return bool(cls.SYMBOL_PATTERN.match(symbol))
    
    @classmethod
    def validate_pattern_name(cls, pattern: str) -> bool:
        """
        Validate candlestick pattern name
        
        Args:
            pattern: Pattern name to validate
            
        Returns:
            bool: True if valid
        """
        if not pattern or not isinstance(pattern, str):
            return False
        
        return bool(cls.PATTERN_NAME_PATTERN.match(pattern.strip().upper()))
    
    @classmethod
    def validate_date(cls, date_str: str) -> bool:
        """
        Validate date format (YYYY-MM-DD)
        
        Args:
            date_str: Date string to validate
            
        Returns:
            bool: True if valid format
        """
        if not date_str or not isinstance(date_str, str):
            return False
        
        return bool(cls.DATE_PATTERN.match(date_str.strip()))
    
    @classmethod
    def validate_percentage(cls, value: Any, min_val: float = 0.1, max_val: float = 50.0) -> bool:
        """
        Validate percentage value
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            bool: True if valid
        """
        try:
            num_val = float(value)
            return min_val <= num_val <= max_val
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def sanitize_string(cls, input_str: str, max_length: int = 100) -> str:
        """
        Sanitize string input
        
        Args:
            input_str: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            str: Sanitized string
        """
        if not isinstance(input_str, str):
            return ""
        
        # Remove HTML tags and escape HTML entities
        sanitized = html.escape(input_str.strip())
        
        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized


class SecurityMiddleware:
    """Security middleware for additional protection"""
    
    @staticmethod
    def validate_request_size(max_content_length: int = 16 * 1024 * 1024):
        """
        Decorator to validate request content length
        
        Args:
            max_content_length: Maximum allowed content length in bytes
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if request.content_length and request.content_length > max_content_length:
                    logger.warning(f"Request too large: {request.content_length} bytes from {request.remote_addr}")
                    return jsonify({'error': 'Request entity too large'}), 413
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def validate_symbol_input(func):
        """Decorator to validate symbol input in request"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            symbol = request.args.get('symbol') or request.json.get('symbol') if request.is_json else None
            
            if symbol and not InputValidator.validate_symbol(symbol):
                logger.warning(f"Invalid symbol format: {symbol} from {request.remote_addr}")
                return jsonify({'error': 'Invalid symbol format'}), 400
                
            return func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def validate_pattern_input(func):
        """Decorator to validate pattern input in request"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            pattern = request.args.get('pattern') or request.json.get('pattern') if request.is_json else None
            
            if pattern and not InputValidator.validate_pattern_name(pattern):
                logger.warning(f"Invalid pattern format: {pattern} from {request.remote_addr}")
                return jsonify({'error': 'Invalid pattern format'}), 400
                
            return func(*args, **kwargs)
        return wrapper


class CSRFProtection:
    """Simple CSRF protection for API endpoints"""
    
    @staticmethod
    def require_csrf_token(func):
        """
        Decorator to require CSRF token for state-changing operations
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip CSRF for GET requests
            if request.method == 'GET':
                return func(*args, **kwargs)
            
            # Check for CSRF token in headers
            csrf_token = request.headers.get('X-CSRF-Token')
            expected_token = request.headers.get('X-Requested-With')
            
            # Simple CSRF protection - require XMLHttpRequest header
            if not expected_token or expected_token != 'XMLHttpRequest':
                logger.warning(f"Missing CSRF protection headers from {request.remote_addr}")
                return jsonify({'error': 'CSRF protection required'}), 403
                
            return func(*args, **kwargs)
        return wrapper


class APIKeyAuth:
    """API key authentication for enhanced security"""
    
    def __init__(self, valid_keys: List[str] = None):
        self.valid_keys = valid_keys or []
    
    def require_api_key(self, func):
        """Decorator to require valid API key"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.valid_keys:
                # API key auth not configured, allow request
                return func(*args, **kwargs)
            
            api_key = request.headers.get('X-API-Key')
            
            if not api_key or api_key not in self.valid_keys:
                logger.warning(f"Invalid or missing API key from {request.remote_addr}")
                return jsonify({'error': 'Invalid or missing API key'}), 401
                
            return func(*args, **kwargs)
        return wrapper


def init_security(app):
    """Initialize security configurations for Flask app"""
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "font-src 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        return response
    
    # Request logging for security monitoring
    @app.before_request
    def log_request():
        """Log requests for security monitoring"""
        if current_app.debug:
            return
            
        # Log suspicious requests
        user_agent = request.headers.get('User-Agent', '')
        if len(user_agent) > 500 or 'bot' in user_agent.lower():
            logger.info(f"Suspicious request from {request.remote_addr}: {user_agent[:100]}")
    
    logger.info("Security middleware initialized")


# Utility functions for enhanced validation
def validate_request_data(required_fields: List[str], optional_fields: List[str] = None) -> Dict[str, Any]:
    """
    Validate and extract request data
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        
    Returns:
        dict: Validated data
        
    Raises:
        ValueError: If validation fails
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    if not data:
        raise ValueError("No data provided")
    
    result = {}
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
        result[field] = InputValidator.sanitize_string(str(data[field]))
    
    # Check optional fields
    if optional_fields:
        for field in optional_fields:
            if field in data and data[field]:
                result[field] = InputValidator.sanitize_string(str(data[field]))
    
    return result


def is_safe_redirect_url(url: str) -> bool:
    """
    Check if URL is safe for redirects
    
    Args:
        url: URL to check
        
    Returns:
        bool: True if safe
    """
    if not url:
        return False
    
    # Only allow relative URLs or same domain
    if url.startswith('/'):
        return True
    
    # Block external redirects
    return False