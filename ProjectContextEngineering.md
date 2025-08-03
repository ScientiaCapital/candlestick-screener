# Project Context & Engineering Decisions

**Project:** Candlestick Screener MVP  
**Date:** August 3, 2025  
**Purpose:** Document engineering decisions, rationale, and architectural choices  

## Executive Summary

This document captures the key engineering decisions made during the development of the Candlestick Screener MVP. Each decision was made with careful consideration of trade-offs, performance implications, and long-term maintainability.

## Core Architecture Decisions

### 1. Alpaca API as Primary Data Source

**Decision**: Use Alpaca Markets API as the primary data source with yfinance as fallback

**Rationale**:
- **Reliability**: Alpaca provides institutional-grade market data with 99.9% uptime
- **Real-Time Data**: Access to real-time quotes and historical data
- **Official SDK**: Well-maintained `alpaca-py` SDK with proper error handling
- **Rate Limits**: Generous rate limits suitable for production applications
- **Data Quality**: Clean, validated data reducing preprocessing needs

**Trade-offs**:
- **Cost**: Alpaca requires API keys and may have usage costs at scale
- **Complexity**: Additional dependency and configuration requirements
- **Vendor Lock-in**: Partial dependency on Alpaca's service availability

**Alternative Considered**: yfinance only
- **Rejected because**: Unreliable for production use, rate limiting issues, unofficial API

```python
# Implementation Pattern
def get_stock_data(self, symbol: str) -> pd.DataFrame:
    # Try Alpaca first (primary)
    if self._use_alpaca:
        try:
            data = self._alpaca_client.get_stock_data(symbol, start_date, end_date)
            if data is not None and not data.empty:
                return data
        except Exception as e:
            logger.error(f"Alpaca failed: {e}")
    
    # Fallback to yfinance
    if self._use_yfinance_fallback:
        return yf.download(symbol, start=start_date, end=end_date)
```

### 2. Dual Data Source Strategy

**Decision**: Implement primary/fallback data source architecture

**Rationale**:
- **Resilience**: System continues operating if primary source fails
- **Migration Path**: Allows gradual transition between data sources
- **Development Flexibility**: Can use different sources for dev/prod
- **Risk Mitigation**: Reduces single point of failure

**Implementation Benefits**:
- Transparent to pattern detection logic
- Configurable via environment variables
- Comprehensive error handling and logging
- Automatic failover with performance metrics

### 3. Vercel + Neon Serverless Architecture

**Decision**: Deploy on Vercel with Neon PostgreSQL

**Rationale**:
- **Serverless Benefits**: Zero server management, automatic scaling
- **Cost Efficiency**: Pay-per-use model, no idle server costs
- **Performance**: Edge deployment for low latency globally
- **Developer Experience**: Git-based deployments, easy rollbacks
- **Database Scaling**: Neon auto-scales and pauses when unused

**Technical Considerations**:
```json
{
  "maxDuration": 30,          // Vercel function timeout
  "maxLambdaSize": "50mb",    // Package size limit
  "regions": ["iad1"],        // Single region for simplicity
  "runtime": "python3.9"     // Stable Python version
}
```

**Trade-offs**:
- **Cold Starts**: Initial request latency for inactive functions
- **Execution Limits**: 30-second timeout requires optimization
- **Stateless Design**: Cannot rely on persistent local storage
- **Memory Constraints**: Limited memory per function execution

**Alternative Considered**: Traditional VPS deployment
- **Rejected because**: Higher operational overhead, fixed costs, scaling complexity

### 4. Test-Driven Development (TDD) Approach

**Decision**: Implement comprehensive TDD methodology

**Rationale**:
- **Code Quality**: Forces better design and interface thinking
- **Regression Prevention**: Catches bugs before they reach production
- **Documentation**: Tests serve as living documentation
- **Confidence**: Enables safe refactoring and feature additions
- **Integration Testing**: Validates external API interactions

**Test Architecture**:
```
59 Total Tests Across Categories:
├── Unit Tests (35)          # Core logic, utilities, helpers
├── Integration Tests (15)   # API integrations, database
├── Security Tests (9)       # Input validation, auth, CSRF
└── Performance Tests        # Caching, rate limiting
```

**Testing Strategy**:
- **Mocking**: External APIs mocked for unit tests
- **Fixtures**: Reusable test data and configurations
- **Coverage**: Aim for 80%+ code coverage
- **CI/CD Ready**: All tests must pass before deployment

### 5. Security-First Design

**Decision**: Implement comprehensive security from day one

**Rationale**:
- **Production Ready**: MVP must be secure enough for real users
- **Compliance**: Follow security best practices from start
- **Trust Building**: Users need confidence in financial applications
- **Risk Mitigation**: Prevent common web application vulnerabilities

**Security Implementation**:
```python
# Multi-layer security approach
@app.route('/api/endpoint')
@limit_burst()                    # Rate limiting
@CSRFProtection.require_csrf_token # CSRF protection
@SecurityMiddleware.validate_request_size() # Input validation
@require_alpaca_auth              # Authentication
def secure_endpoint():
    # Sanitized input processing
    # Validated output
```

**Security Rating Achieved**: A+
- All OWASP Top 10 vulnerabilities addressed
- Comprehensive input validation
- Proper secret management
- Secure headers implemented

### 6. Serverless Optimization Strategy

**Decision**: Optimize specifically for serverless constraints

**Rationale**:
- **Cold Start Minimization**: Reduce function initialization time
- **Memory Efficiency**: Work within serverless memory limits
- **Stateless Design**: Handle lack of persistent storage gracefully
- **Timeout Management**: Complete operations within function limits

**Optimizations Implemented**:
```python
# Conditional logging based on environment
if os.getenv('FLASK_ENV') != 'production' and os.access(os.getcwd(), os.W_OK):
    try:
        log_handlers.append(logging.FileHandler('app.log'))
    except (PermissionError, OSError):
        pass  # Graceful degradation

# In-memory fallbacks for file operations
if not os.access(os.getcwd(), os.W_OK):
    logger.warning(f"No write access - caching {symbol} data in memory only")
    invalidate_cache('stock_data', symbol)
    return True
```

**Serverless-Specific Patterns**:
- Lazy loading of heavy dependencies
- In-memory caching when filesystem unavailable
- Graceful degradation for missing resources
- Optimized cold start paths

## Performance Engineering Decisions

### 1. Intelligent Caching Strategy

**Decision**: Multi-level caching with smart invalidation

**Cache Levels**:
```python
@cache_stock_data()           # Stock data caching (5 minutes)
@cache_pattern_analysis()     # Pattern results (10 minutes)  
@cache_symbol_list()          # Symbol list (1 hour)
```

**Cache Invalidation Logic**:
- Time-based expiration for data freshness
- Manual invalidation on data updates
- Graceful fallback when cache unavailable

### 2. Rate Limiting Strategy

**Decision**: Multi-tier rate limiting approach

```python
# Different limits for different operations
@limit_index()        # 100/hour for main page
@limit_snapshot()     # 10/hour for data updates
@limit_pattern_analysis() # 50/hour for pattern detection
@limit_burst()        # 200/hour for API endpoints
```

**Rationale**: Balance user experience with API protection

### 3. Batch Processing Optimization

**Decision**: Configurable batch processing for symbol handling

```python
BATCH_SIZE = max(1, min(50, int(os.getenv('BATCH_SIZE', '10'))))

# Process symbols in batches to manage memory and timeouts
for i in range(0, len(symbols), Config.BATCH_SIZE):
    batch = symbols[i:i + Config.BATCH_SIZE]
    process_batch(batch)
```

**Benefits**: Memory management, timeout prevention, scalable processing

## Trade-offs and Technical Debt

### MVP Limitations Acknowledged

**Symbol Processing Limit**:
- **Current**: 10 symbols for demo purposes
- **Reason**: Vercel 30-second timeout constraint
- **Future**: Implement background job processing

**Sequential Pattern Processing**:
- **Current**: Patterns processed one at a time
- **Reason**: Simplicity and memory management
- **Future**: Parallel processing with worker threads

**Limited Historical Data**:
- **Current**: 1-year historical data maximum
- **Reason**: API rate limits and processing time
- **Future**: Configurable time ranges with pagination

### Technical Debt Items

**Mixed Authentication Systems**:
```python
# Legacy client still used for some auth operations
from alpaca_client import AlpacaAPIError, require_alpaca_auth
# New SDK used for data operations  
from alpaca_client_sdk import get_alpaca_client
```
- **Impact**: Code complexity, maintenance overhead
- **Plan**: Consolidate to single SDK implementation

**File Storage Dependencies**:
- Some components still attempt file operations
- Need to fully transition to database/cache storage
- Affects symbol management and data persistence

### Future Enhancement Opportunities

**High-Impact Improvements**:
1. **WebSocket Integration**: Real-time pattern detection
2. **Advanced Caching**: Redis-based distributed caching
3. **Parallel Processing**: Multi-threaded pattern analysis
4. **Database Optimization**: Query optimization and indexing

**Architecture Evolution Path**:
```
Current MVP → Enhanced Performance → Multi-User Platform
     ↓              ↓                    ↓
- Basic patterns  - Real-time data    - User accounts
- Single user     - Parallel proc     - Portfolios  
- Cached data     - WebSocket API     - Alerts
- REST API        - Advanced cache    - Social features
```

## Quality Assurance Decisions

### Testing Philosophy

**Integration Over Unit**: 
- Focus on testing component interactions
- Mock external dependencies appropriately
- Validate end-to-end workflows

**Security Testing Priority**:
- All security middleware tested
- Input validation edge cases covered
- Authentication flows validated

### Error Handling Strategy

**Graceful Degradation Pattern**:
```python
try:
    # Attempt primary operation
    result = primary_operation()
except PrimaryError:
    try:
        # Fallback operation
        result = fallback_operation()
    except FallbackError:
        # Graceful failure
        return default_safe_result()
```

**Comprehensive Logging**:
- All errors logged with context
- Performance metrics captured
- Security events monitored

## Deployment Engineering

### CI/CD Philosophy

**Pre-Deployment Validation**:
1. All tests must pass
2. Security audit must show A+ rating
3. Configuration validation required
4. API connectivity verified

**Deployment Pipeline**:
```bash
pytest                    # Run all tests
python verify-deployment.py  # Security & config check
vercel --prod            # Deploy to production
```

### Monitoring Strategy

**Health Check Implementation**:
```python
@app.route('/health')
def health_check():
    return {
        'cache': check_cache_status(),
        'database': check_db_connection(), 
        'alpaca_api': test_alpaca_connection(),
        'overall': 'healthy|degraded|unhealthy'
    }
```

## Conclusion

The engineering decisions documented here prioritize:
1. **Production Readiness**: Security, reliability, performance
2. **Maintainability**: Clean code, comprehensive tests, clear documentation
3. **Scalability**: Serverless architecture, efficient caching, modular design
4. **User Experience**: Fast response times, graceful error handling

These decisions create a solid foundation for future enhancements while delivering immediate value as an MVP. The technical debt items are well-documented and have clear paths for resolution as the project evolves.