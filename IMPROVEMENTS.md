# Candlestick Screener Improvements

## Overview
This document outlines the planned improvements to the Candlestick Screener application, focusing on configuration management, caching, and rate limiting.

## 1. Environment Configuration (.env)

### Tasks
- [ ] Create `.env` file with the following variables:
  ```
  # Application Settings
  FLASK_APP=app.py
  FLASK_ENV=development
  FLASK_DEBUG=True
  
  # Batch Processing
  BATCH_SIZE=10
  
  # Cache Settings
  CACHE_TYPE=redis
  CACHE_REDIS_URL=redis://localhost:6379/0
  CACHE_TIMEOUT=300
  
  # Rate Limiting
  RATELIMIT_STORAGE_URL=redis://localhost:6379/0
  RATELIMIT_DEFAULT=200/hour
  RATELIMIT_STORAGE_OPTIONS={"socket_connect_timeout": 30}
  
  # API Keys (if needed)
  ALPHA_VANTAGE_API_KEY=your_key_here
  
  # Security
  SECRET_KEY=your_secret_key_here
  ```

### Considerations
- Ensure `.env` is in `.gitignore`
- Create `.env.example` for documentation
- Add environment variable validation in the application
- Document all environment variables

## 2. Redis Caching Implementation

### Tasks
- [ ] Add Redis dependencies to `requirements.txt`:
  ```
  redis==5.0.1
  Flask-Caching==2.1.0
  ```

- [ ] Implement Redis caching:
  - [ ] Create cache configuration class
  - [ ] Implement cache decorators for expensive operations
  - [ ] Add cache invalidation strategies
  - [ ] Implement cache key management
  - [ ] Add cache statistics monitoring

### Cache Strategy
1. Stock Data Caching:
   - Cache key: `stock_data:{symbol}:{start_date}:{end_date}`
   - TTL: 1 hour
   - Invalidate on new data fetch

2. Pattern Analysis Results:
   - Cache key: `pattern:{symbol}:{pattern_name}`
   - TTL: 15 minutes
   - Invalidate on new data

3. Symbol List:
   - Cache key: `symbols:list`
   - TTL: 24 hours
   - Invalidate on symbol list update

## 3. Rate Limiting Implementation

### Tasks
- [ ] Add rate limiting dependencies:
  ```
  Flask-Limiter==3.5.0
  ```

- [ ] Implement rate limiting:
  - [ ] Configure rate limit storage
  - [ ] Define rate limit rules
  - [ ] Add rate limit headers
  - [ ] Implement rate limit error handling
  - [ ] Add rate limit monitoring

### Rate Limit Rules
1. API Endpoints:
   - `/snapshot`: 10 requests per hour
   - `/`: 200 requests per hour
   - Pattern analysis: 100 requests per hour

2. IP-based limits:
   - Default: 200 requests per hour
   - Burst: 50 requests per minute

3. User-based limits (if implemented):
   - Authenticated users: 1000 requests per hour
   - Unauthenticated users: 200 requests per hour

## Implementation Order

1. Environment Configuration
   - Create `.env` and `.env.example`
   - Update configuration management
   - Add validation

2. Redis Caching
   - Set up Redis connection
   - Implement basic caching
   - Add cache management
   - Implement invalidation

3. Rate Limiting
   - Configure rate limit storage
   - Implement basic limits
   - Add monitoring
   - Implement error handling

## Testing Strategy

1. Unit Tests:
   - Cache hit/miss scenarios
   - Rate limit enforcement
   - Configuration validation

2. Integration Tests:
   - Redis connection
   - Rate limit storage
   - Cache invalidation

3. Load Tests:
   - Rate limit effectiveness
   - Cache performance
   - System stability

## Monitoring and Maintenance

1. Cache Monitoring:
   - Hit/miss ratios
   - Memory usage
   - Eviction rates

2. Rate Limit Monitoring:
   - Request counts
   - Limit breaches
   - IP distribution

3. System Health:
   - Redis connection status
   - Memory usage
   - Error rates

## Rollout Strategy

1. Development:
   - Implement in development environment
   - Test with sample data
   - Verify configurations

2. Staging:
   - Deploy to staging environment
   - Load test
   - Monitor performance

3. Production:
   - Gradual rollout
   - Monitor metrics
   - Adjust as needed

## Success Criteria

1. Performance:
   - Reduced response times
   - Lower server load
   - Better resource utilization

2. Stability:
   - No memory leaks
   - Consistent performance
   - Reliable rate limiting

3. Monitoring:
   - Clear metrics
   - Actionable alerts
   - Easy troubleshooting 