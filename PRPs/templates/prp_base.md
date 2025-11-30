# PRP: [Feature Name]

**Date**: 2025-11-30
**Author**: Claude + Tim
**Status**: [Draft | In Progress | Complete]
**Priority**: [P0-Critical | P1-High | P2-Medium | P3-Low]

---

## 1. Overview

### 1.1 What
Brief description of what this feature does (1-2 sentences).

### 1.2 Why
Problem this feature solves and business value it provides.

### 1.3 Who
Target users and their use cases.

**User Stories**:
- As a [user type], I want to [action] so that [benefit]
- As a [user type], I want to [action] so that [benefit]

---

## 2. Technical Requirements

### 2.1 Functional Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

### 2.2 Non-Functional Requirements
- **Performance**: Response time < 2s, bundle size < 50KB
- **Security**: Input validation, output sanitization, rate limiting
- **Scalability**: Handle 1000 concurrent users
- **Availability**: 99.9% uptime
- **Compatibility**: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+)

### 2.3 Dependencies
- **External APIs**: Alpaca (stock data), NREL (energy data if applicable)
- **NPM Packages**: [list new packages if any]
- **Python Libraries**: [list new libraries if any]
- **Infrastructure**: Redis (caching), PostgreSQL (storage)

### 2.4 Constraints
- NO OpenAI models
- API keys in .env only
- Serverless function timeout: 10s
- Database query limit: 1000 rows per request

---

## 3. Component Design

### 3.1 Frontend Components (React + TypeScript)

#### Component: [ComponentName]

**Location**: `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/app/components/[ComponentName].tsx`

**Purpose**: [Brief description]

**Props Interface**:
```typescript
interface [ComponentName]Props {
  // Required props
  data: DataType;
  onAction: (param: ParamType) => void;

  // Optional props
  className?: string;
  loading?: boolean;
}
```

**State Management**:
```typescript
const [state, setState] = useState<StateType>(initialState);
const [loading, setLoading] = useState<boolean>(false);
const [error, setError] = useState<string | null>(null);
```

**Key Methods**:
- `handleAction()` - Description
- `validateInput()` - Description
- `fetchData()` - Description

**Styling**: Tailwind CSS classes
- Mobile-first responsive design
- Dark mode support (if applicable)
- Accessibility (ARIA labels, keyboard navigation)

**Example Usage**:
```tsx
<ComponentName
  data={myData}
  onAction={handleAction}
  className="custom-class"
/>
```

**Tests**:
- [ ] Render test
- [ ] User interaction test
- [ ] Error state test
- [ ] Loading state test
- [ ] Accessibility test

---

### 3.2 Backend API Routes (Next.js Serverless)

#### API Route: `/api/[route-name]`

**Location**: `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/app/api/[route-name]/route.ts`

**Method**: `GET | POST | PUT | DELETE`

**Request Schema**:
```typescript
interface RequestBody {
  // Required fields
  field1: string;
  field2: number;

  // Optional fields
  field3?: boolean;
}
```

**Response Schema**:
```typescript
interface SuccessResponse {
  data: DataType;
  timestamp: string;
}

interface ErrorResponse {
  error: string;
  code: string;
}
```

**Implementation**:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { validateInput, sanitizeInput } from '@/lib/security';

export async function POST(request: NextRequest) {
  try {
    // 1. Parse request
    const body = await request.json();

    // 2. Validate input
    if (!validateInput(body)) {
      return NextResponse.json(
        { error: 'Invalid input', code: 'VALIDATION_ERROR' },
        { status: 400 }
      );
    }

    // 3. Sanitize input
    const sanitized = sanitizeInput(body);

    // 4. Process request
    const result = await processRequest(sanitized);

    // 5. Return response
    return NextResponse.json({
      data: result,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', code: 'INTERNAL_ERROR' },
      { status: 500 }
    );
  }
}
```

**Security Measures**:
- [ ] Input validation
- [ ] Input sanitization
- [ ] Rate limiting
- [ ] Authentication (if required)
- [ ] CORS headers
- [ ] Error message sanitization

**Tests**:
- [ ] Valid request test
- [ ] Invalid request test
- [ ] Missing field test
- [ ] Unauthorized test (if auth required)
- [ ] Rate limit test

---

### 3.3 Python Backend (Pattern Detection / Data Processing)

#### Module: `[module_name].py`

**Location**: `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/[module_name].py`

**Purpose**: [Brief description]

**Functions**:

```python
def process_data(
    input_data: pd.DataFrame,
    config: dict
) -> dict:
    """
    Process stock data and detect patterns

    Args:
        input_data: DataFrame with OHLCV data
        config: Configuration dictionary

    Returns:
        dict: {pattern_name: {confidence: float, signal: str}}

    Raises:
        ValueError: If input data is invalid
        KeyError: If required columns missing
    """
    # Validation
    if not validate_ohlcv_data(input_data):
        raise ValueError("Invalid OHLCV data")

    # Processing
    patterns = {}

    # Pattern detection logic here

    return patterns
```

**Error Handling**:
```python
try:
    result = process_data(data, config)
except ValueError as e:
    logger.error(f"Validation error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

**Tests**:
- [ ] Valid input test
- [ ] Invalid input test
- [ ] Edge case tests (empty data, single row, etc.)
- [ ] Performance test (large dataset)

---

## 4. Alpaca SDK Integration

### 4.1 Data Fetching

**Function**: `fetch_stock_data()`

```python
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import os

def fetch_stock_data(
    symbols: list[str],
    timeframe: str = '1Day',
    days_back: int = 30
) -> dict:
    """
    Fetch stock data from Alpaca API

    Args:
        symbols: List of stock symbols
        timeframe: Bar timeframe (1Min, 5Min, 1Hour, 1Day)
        days_back: Number of days of historical data

    Returns:
        dict: {symbol: DataFrame with OHLCV data}
    """
    client = StockHistoricalDataClient(
        api_key=os.getenv('ALPACA_API_KEY'),
        secret_key=os.getenv('ALPACA_SECRET_KEY')
    )

    request_params = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame[timeframe],
        start=datetime.now() - timedelta(days=days_back),
        end=datetime.now()
    )

    bars = client.get_stock_bars(request_params)

    # Convert to DataFrame
    data = {}
    for symbol in symbols:
        data[symbol] = bars.df[symbol] if symbol in bars.df else None

    return data
```

### 4.2 WebSocket Streaming (Optional)

```python
from alpaca.data.live import StockDataStream

async def stream_stock_data(symbols: list[str]):
    """Stream real-time stock data"""
    stream = StockDataStream(
        api_key=os.getenv('ALPACA_API_KEY'),
        secret_key=os.getenv('ALPACA_SECRET_KEY')
    )

    async def handle_bar(bar):
        print(f"Bar: {bar}")
        # Process bar data

    stream.subscribe_bars(handle_bar, *symbols)
    await stream.run()
```

### 4.3 Rate Limiting Strategy

**Alpaca Limits**: 200 requests/minute

**Implementation**:
```python
import time
from functools import wraps

def rate_limit(max_per_minute: int = 200):
    """Decorator to enforce rate limiting"""
    min_interval = 60.0 / max_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_per_minute=200)
def fetch_alpaca_data(symbol: str):
    # Alpaca API call
    pass
```

---

## 5. Security Considerations

### 5.1 Input Validation

**Stock Symbol Validation**:
```typescript
export function validateStockSymbol(symbol: string): boolean {
  // Only uppercase letters, max 5 characters
  const symbolRegex = /^[A-Z]{1,5}$/;
  return symbolRegex.test(symbol);
}
```

**Timeframe Validation**:
```typescript
const VALID_TIMEFRAMES = ['1Min', '5Min', '15Min', '1Hour', '1Day'];

export function validateTimeframe(timeframe: string): boolean {
  return VALID_TIMEFRAMES.includes(timeframe);
}
```

### 5.2 Output Sanitization

```typescript
export function sanitizeOutput(text: string): string {
  return text
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}
```

### 5.3 Rate Limiting

**Middleware**:
```typescript
import rateLimit from 'express-rate-limit';

export const apiLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 60, // 60 requests per minute
  message: 'Too many requests, please try again later'
});
```

### 5.4 Authentication (if required)

```typescript
import { auth } from '@/lib/auth';

export async function authenticateRequest(request: NextRequest) {
  const token = request.headers.get('authorization');

  if (!token) {
    throw new Error('Unauthorized');
  }

  const user = await auth.verifyToken(token);

  if (!user) {
    throw new Error('Invalid token');
  }

  return user;
}
```

---

## 6. Caching Strategy

### 6.1 Cache Layers

| Layer | Storage | TTL | Purpose |
|-------|---------|-----|---------|
| Browser | LocalStorage | 1 hour | User preferences |
| CDN | Vercel Edge | 5 minutes | API responses |
| Application | Redis | 1-5 minutes | Market data |
| Database | PostgreSQL | 1 hour | Pattern results |

### 6.2 Redis Caching Implementation

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

export async function getCached<T>(
  key: string,
  fetchFn: () => Promise<T>,
  ttl: number = 300
): Promise<T> {
  // Try cache first
  const cached = await redis.get(key);
  if (cached) {
    return JSON.parse(cached);
  }

  // Fetch fresh data
  const data = await fetchFn();

  // Cache for next time
  await redis.setex(key, ttl, JSON.stringify(data));

  return data;
}
```

### 6.3 Cache Invalidation

**When to invalidate**:
- Market open/close
- Pattern detection settings change
- Manual refresh by user

**Implementation**:
```typescript
export async function invalidateCache(pattern: string) {
  const keys = await redis.keys(pattern);
  if (keys.length > 0) {
    await redis.del(...keys);
  }
}
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Frontend**:
```bash
npm test -- <ComponentName>.test.tsx --coverage
```

**Backend**:
```bash
pytest tests/test_<module>.py -v --cov
```

**Coverage Target**: > 80%

### 7.2 Integration Tests

```typescript
// integration.test.ts
describe('Pattern Detection Flow', () => {
  it('fetches data, detects patterns, returns results', async () => {
    // 1. Fetch data from Alpaca
    const data = await fetchStockData(['AAPL']);

    // 2. Detect patterns
    const patterns = await detectPatterns(data);

    // 3. Verify results
    expect(patterns).toBeDefined();
    expect(patterns['AAPL']).toHaveLength(greaterThan(0));
  });
});
```

### 7.3 Security Tests

```bash
# SQL Injection
curl -X POST http://localhost:3000/api/scan \
  -d '{"symbol": "AAPL'; DROP TABLE users; --"}'

# XSS
curl -X POST http://localhost:3000/api/scan \
  -d '{"symbol": "<script>alert('XSS')</script>"}'

# Rate Limiting
for i in {1..100}; do
  curl http://localhost:3000/api/scan
done
```

### 7.4 Performance Tests

```bash
# Load test with k6
k6 run --vus 100 --duration 30s load-test.js

# Bundle size analysis
npm run analyze
```

---

## 8. Deployment Plan

### 8.1 Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Security audit complete (A+ rating)
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] Database migrations ready (if any)

### 8.2 Deployment Steps

```bash
# 1. Run full validation
/validate

# 2. Build production
npm run build

# 3. Deploy to Vercel
vercel --prod

# 4. Verify deployment
curl https://candlestick-screener.vercel.app/api/health

# 5. Monitor logs
vercel logs --follow
```

### 8.3 Rollback Plan

If issues occur:

```bash
# Rollback to previous deployment
vercel rollback

# Or deploy specific commit
vercel --prod --git-commit <commit-hash>
```

### 8.4 Monitoring

**Metrics to Track**:
- API response time (target: < 2s)
- Error rate (target: < 0.1%)
- Cache hit rate (target: > 80%)
- Active users
- API quota usage (Alpaca)

**Tools**:
- Vercel Analytics
- Sentry (error tracking)
- Alpaca Dashboard (API usage)

---

## 9. Success Metrics

### 9.1 Technical Metrics

- [ ] Page load time < 2s
- [ ] API response time < 1s
- [ ] Test coverage > 80%
- [ ] Security rating: A+
- [ ] Zero critical vulnerabilities
- [ ] Bundle size < 500KB

### 9.2 User Metrics

- [ ] User satisfaction > 4/5
- [ ] Feature adoption > 50% (within 30 days)
- [ ] Error reports < 5 per week
- [ ] Average session time > 5 minutes

### 9.3 Business Metrics

- [ ] User retention +10%
- [ ] Engagement +20%
- [ ] Support tickets -15%

---

## 10. Future Enhancements

**Phase 2 Ideas**:
- Advanced pattern combinations (AND/OR logic)
- Custom pattern creation
- Pattern backtesting
- Email/SMS alerts
- Social sharing

**Technical Debt**:
- None identified (or list items)

---

## Appendix

### A. References
- Alpaca API Docs: https://docs.alpaca.markets/
- Next.js Docs: https://nextjs.org/docs
- React Testing Library: https://testing-library.com/react

### B. Glossary
- **OHLCV**: Open, High, Low, Close, Volume
- **Candlestick Pattern**: Visual pattern in price charts
- **Serverless**: Functions that run on-demand without server management

### C. Related PRPs
- [Link to related PRPs if any]
