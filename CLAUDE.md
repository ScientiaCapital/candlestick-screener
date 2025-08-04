# Candlestick Screener - Claude Context Guide

**Version:** 2.0.0  
**Last Updated:** August 4, 2025  
**Purpose:** Enable future Claude sessions to understand and work with this project immediately  

## Project Overview

The Candlestick Screener is a modern React/Next.js 14 application with TypeScript that screens stocks for candlestick patterns using real-time market data. It features a professional frontend with Python serverless API endpoints, optimized for Vercel deployment.

### Core Functionality
- **Pattern Detection**: Professional React components for candlestick pattern screening
- **Real-Time Data**: Python serverless APIs with market data integration
- **Stock Screening**: Interactive TypeScript interface for pattern analysis
- **Modern UI**: React/Next.js 14 with Tailwind CSS and Heroicons
- **Component Architecture**: PatternSelector, StockScanner, and ResultsTable components

## Technology Stack

### Frontend
- **React**: ^18 with modern hooks and functional components
- **Next.js**: 14.2.5 with App Router and TypeScript support
- **TypeScript**: ^5.8.3 for type safety and developer experience
- **Tailwind CSS**: ^3.4.6 for responsive, utility-first styling
- **Heroicons**: ^2.2.0 for consistent iconography

### Backend APIs
- **Python**: Serverless functions in /api directory
- **Vercel Runtime**: Python serverless environment
- **Market Data**: Integration ready for external APIs

### Development & Testing
- **Jest**: ^29.7.0 for comprehensive testing framework
- **Testing Library**: React testing utilities with user-event support
- **ESLint**: Next.js configuration for code quality
- **PostCSS**: Build pipeline with Autoprefixer

### Architecture
- **Frontend**: React/Next.js 14 application with TypeScript
- **APIs**: Python serverless functions in /api directory
- **Deployment**: Vercel serverless platform
- **Styling**: Tailwind CSS with responsive design patterns

## Architecture Overview

### Serverless-First Design
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Frontend  │────│ API Routes   │────│ Data Layer  │
│  (Browser)  │    │  (Vercel)    │    │  (Alpaca)   │
└─────────────┘    └──────────────┘    └─────────────┘
                          │
                   ┌──────────────┐
                   │  Security    │
                   │  & Caching   │
                   └──────────────┘
```

### Key Components
- **StockDataManager**: Handles data fetching with dual sources
- **PatternAnalyzer**: Processes candlestick patterns using pandas-ta
- **Security Layer**: Input validation, CSRF, rate limiting
- **Cache Manager**: Intelligent caching with invalidation
- **Rate Limiter**: Prevents API abuse and DoS attacks

## Key Files & Purposes

### Core Application
- **`app/`**: React/Next.js application with components and pages
- **`api/`**: Python serverless API endpoints (health, patterns, scan, symbols)
- **`patterns.py`**: Dictionary of 60+ candlestick patterns

### Data & API Integration
- **`alpaca_client_sdk.py`**: Official Alpaca SDK integration
- **`alpaca_client.py`**: Legacy Alpaca client (still used for auth)
- **`database.py`**: Database connection and operations

### Security & Performance
- **`security.py`**: Comprehensive security middleware
- **`cache_manager.py`**: Intelligent caching system
- **`rate_limiter.py`**: API rate limiting configuration

### Infrastructure
- **`vercel.json`**: Vercel deployment configuration
- **`requirements.txt`**: Python dependencies
- **`pytest.ini`**: Test configuration

### Documentation
- **`SECURITY_AUDIT_REPORT.md`**: Security audit results (A+ rating)
- **`DEPLOYMENT.md`**: Deployment guide and checklist
- **`IMPROVEMENTS.md`**: Future enhancement roadmap

## Common Workflows

### Adding New Candlestick Patterns
1. Add pattern to `patterns.py` dictionary
2. Verify pandas-ta supports the pattern
3. Add tests in `tests/test_patterns.py`
4. Update documentation

### Data Source Management
```python
# Primary: Alpaca API
data = stock_manager.get_stock_data(symbol, start_date, end_date)

# Automatic fallback to yfinance if Alpaca fails
# Caching applied automatically via decorators
# Input validation via security middleware
```

### Testing Workflow (TDD Approach)
```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_alpaca_integration.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Deployment Process
1. Run security audit: `python verify-deployment.py`
2. Validate configuration: `pytest tests/test_config.py`
3. Check Alpaca integration: `python quick_test.py`
4. Deploy to Vercel: `vercel --prod`

## Integration Points

### Alpaca SDK Integration
```python
from alpaca_client_sdk import get_alpaca_client

client = get_alpaca_client()
data = client.get_stock_data(symbol, start_date, end_date)
```

### Database Connection (Neon)
```python
from database import DatabaseManager

db = DatabaseManager()
# Automatic connection pooling and serverless optimization
```

### Pattern Analysis
```python
from patterns import candlestick_patterns

# All 60+ patterns available
patterns_to_check = list(candlestick_patterns.keys())
results = pattern_analyzer.batch_process_patterns(df, patterns_to_check)
```

## Testing Architecture (TDD)

### Test Coverage: 59 Tests
- **Integration Tests**: Alpaca API, database connections
- **Unit Tests**: Pattern detection, caching, security
- **API Tests**: Endpoint validation, error handling
- **Security Tests**: Input validation, rate limiting

### Test Categories
```
__tests__/
├── components/
│   ├── PatternSelector.test.tsx    # Pattern selector component tests
│   ├── StockScanner.test.tsx       # Stock scanner component tests
│   └── ResultsTable.test.tsx       # Results table component tests
tests/
├── test_alpaca_integration.py      # Alpaca API integration tests  
├── test_config.py                  # Configuration validation tests
└── test_patterns.py                # Pattern detection tests
```

## Security Measures

### Implemented Protections
- **Input Validation**: All user inputs sanitized and validated
- **CSRF Protection**: Token-based CSRF protection
- **Rate Limiting**: Multiple tiers (burst, sustained, pattern-specific)
- **Security Headers**: CSP, HSTS, X-Frame-Options
- **Environment Security**: No credentials in code
- **API Security**: Alpaca API key protection and validation

### Security Rating: A+
- Comprehensive security audit completed
- All critical and high-risk issues resolved
- Production-ready security posture

## Performance Optimizations

### Serverless Optimizations
- **Cold Start Reduction**: Minimal imports, lazy loading
- **Memory Efficiency**: In-memory caching when filesystem unavailable
- **Timeout Handling**: 30-second Vercel function limit respected
- **Batch Processing**: Configurable batch sizes for symbol processing

### Caching Strategy
- **Multi-Level Caching**: Stock data, pattern analysis, symbol lists
- **Smart Invalidation**: Cache invalidation on data updates
- **Fallback Mechanisms**: Graceful degradation when cache unavailable

## Environment Variables Required

### Production (Required)
```env
# Next.js Configuration  
NODE_ENV=production
NEXT_PUBLIC_API_URL=your-api-base-url

# Alpaca API (Required for MVP)
ALPACA_API_KEY=your-alpaca-api-key
ALPACA_SECRET_KEY=your-alpaca-secret-key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Security
CSRF_SECRET_KEY=your-csrf-secret-key

# Optional Performance
CACHE_REDIS_URL=redis://localhost:6379/0
RATELIMIT_STORAGE_URL=redis://localhost:6379/0
```

### Development (Optional)
```env
NODE_ENV=development
ALPHA_VANTAGE_API_KEY=optional-alpha-vantage-key
LOG_LEVEL=DEBUG
```

## Current MVP Limitations

### Known Constraints
- **Symbol Limit**: Processing limited to 10 symbols for demo
- **Timeout**: 30-second Vercel function limit
- **Pattern Processing**: Sequential processing (could be parallelized)
- **Data History**: Limited to 1-year historical data
- **File Storage**: No persistent file storage in serverless environment

### Technical Debt
- Legacy `alpaca_client.py` still used for authentication
- Mixed async/sync patterns in some modules
- Some test fixtures could be more comprehensive

## Quick Start for New Sessions

1. **Understand Current State**: Review recent commits and test results
2. **Check Configuration**: Verify all environment variables are set
3. **Run Tests**: Execute `pytest` to ensure everything works
4. **Review Security**: Check `SECURITY_AUDIT_REPORT.md` for current status
5. **Test Alpaca**: Run `python quick_test.py` to verify API connectivity

## Future Enhancement Opportunities

### High Priority
- **WebSocket Integration**: Real-time pattern detection
- **Advanced Patterns**: Custom pattern definitions
- **Performance**: Parallel pattern processing
- **User Management**: Authentication and portfolios

### Medium Priority
- **Data Sources**: Additional market data providers
- **Visualization**: Interactive charts and pattern highlighting
- **Alerts**: Email/SMS notifications for pattern matches
- **API Expansion**: More comprehensive REST API

## Troubleshooting Common Issues

### Alpaca API Issues
```python
# Test connection
python quick_test.py

# Check logs
tail -f app.log
```

### Cache Issues
```python
# Clear cache
from cache_manager import cache
cache.clear()
```

### Security Issues
```python
# Validate configuration
python -c "from config import Config; print(Config.validate())"
```

This guide should enable any future Claude session to immediately understand the project structure, make informed decisions, and continue development effectively.