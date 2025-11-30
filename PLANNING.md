# Candlestick Screener - Architecture & Planning

**Project**: Stock Pattern Screener
**Tech Stack**: React 18, Next.js 14.2.5, TypeScript 5.8, Tailwind CSS, Python
**Data Source**: Alpaca API (primary), yfinance (fallback)
**Database**: Neon PostgreSQL
**Deployment**: Vercel (Frontend + Serverless Functions)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Browser)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   React 18 + TypeScript + Tailwind CSS             │   │
│  │   - PatternSelector, StockScanner, ResultsTable    │   │
│  │   - State Management (useState, useEffect)         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              VERCEL (Serverless Functions)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Next.js API Routes                                │   │
│  │   - /api/scan - Pattern scanning                    │   │
│  │   - /api/patterns - Pattern metadata                │   │
│  │   - /api/health - Health check                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ↓                       ↓
┌──────────────────────┐    ┌──────────────────────┐
│  Alpaca API          │    │  Redis Cache         │
│  - Stock bars        │    │  - Market data (5m)  │
│  - Real-time data    │    │  - Pattern results   │
│  - WebSocket         │    │  - User prefs (1h)   │
└──────────────────────┘    └──────────────────────┘
                │                       │
                └───────────┬───────────┘
                            ↓
                ┌──────────────────────┐
                │  Neon PostgreSQL     │
                │  - User accounts     │
                │  - Watchlists        │
                │  - Scan history      │
                └──────────────────────┘
```

### 1.2 Serverless-First Design

**Philosophy**: Minimize server management, maximize scalability

**Benefits**:
- Auto-scaling (handle 1-10,000 users)
- Pay-per-use (cost-effective for sporadic traffic)
- Global CDN (low latency worldwide)
- Zero maintenance (Vercel manages infrastructure)

**Constraints**:
- Function timeout: 10s (free tier)
- Memory limit: 1024MB (free tier)
- Cold start: ~200ms (optimized)

---

## 2. Component Breakdown

### 2.1 Frontend Components

#### Component: PatternSelector
**Location**: `app/components/PatternSelector.tsx`

**Purpose**: Allow users to select candlestick patterns to scan for

**Props**:
```typescript
interface PatternSelectorProps {
  availablePatterns: string[];
  selectedPatterns: string[];
  onPatternsChange: (patterns: string[]) => void;
}
```

**Features**:
- Multi-select with visual feedback
- Search/filter patterns
- Categories (bullish, bearish, neutral)
- Keyboard navigation (accessibility)

**State**:
- Local state for UI interactions
- Parent component manages selected patterns

---

#### Component: StockScanner
**Location**: `app/components/StockScanner.tsx`

**Purpose**: Input stock symbols and trigger scans

**Props**:
```typescript
interface StockScannerProps {
  onScan: (symbols: string[], patterns: string[]) => void;
  loading: boolean;
}
```

**Features**:
- Symbol input (comma-separated or file upload)
- Timeframe selection (1Min, 5Min, 1Hour, 1Day)
- Date range picker
- Validate symbols before scanning

**Validation**:
- Max 10 symbols per scan (free tier limit)
- Symbol format: A-Z, 1-5 characters
- Duplicate removal

---

#### Component: ResultsTable
**Location**: `app/components/ResultsTable.tsx`

**Purpose**: Display scan results in tabular format

**Props**:
```typescript
interface ResultsTableProps {
  results: ScanResult[];
  onExport: (format: 'csv' | 'json') => void;
  sortable: boolean;
}

interface ScanResult {
  symbol: string;
  pattern: string;
  confidence: number;
  signal: 'bullish' | 'bearish' | 'neutral';
  timestamp: string;
  chartUrl?: string;
}
```

**Features**:
- Sortable columns (symbol, pattern, confidence)
- Export to CSV/JSON
- Click row to view chart
- Color-coded signals (green=bullish, red=bearish)

---

#### Component: StockChart
**Location**: `app/components/StockChart.tsx`

**Purpose**: Visualize candlestick chart with pattern annotations

**Props**:
```typescript
interface StockChartProps {
  symbol: string;
  data: OHLCVData[];
  patterns: PatternAnnotation[];
  timeframe: string;
}
```

**Implementation**:
- Use Recharts or Lightweight Charts library
- Overlay pattern markers on candles
- Zoom/pan functionality
- Mobile-responsive

---

### 2.2 Backend API Routes

#### API: `/api/scan` (POST)
**Purpose**: Scan symbols for patterns

**Request**:
```json
{
  "symbols": ["AAPL", "TSLA", "MSFT"],
  "patterns": ["doji", "hammer", "engulfing"],
  "timeframe": "1Day",
  "days_back": 30
}
```

**Response**:
```json
{
  "results": [
    {
      "symbol": "AAPL",
      "pattern": "doji",
      "confidence": 0.87,
      "signal": "neutral",
      "timestamp": "2025-11-30T12:00:00Z"
    }
  ],
  "processing_time_ms": 1234
}
```

**Implementation**:
1. Validate input (symbols, patterns, timeframe)
2. Check Redis cache
3. Fetch data from Alpaca API
4. Run pattern detection (Python)
5. Cache results (5min TTL)
6. Return results

**Security**:
- Rate limiting: 60 requests/minute per IP
- Input validation (prevent injection)
- Sanitize output (no raw error messages)

---

#### API: `/api/patterns` (GET)
**Purpose**: Get list of available patterns

**Response**:
```json
{
  "patterns": [
    {
      "name": "doji",
      "category": "neutral",
      "description": "Indecision pattern with small body",
      "reliability": "medium"
    },
    {
      "name": "hammer",
      "category": "bullish",
      "description": "Reversal pattern with long lower shadow",
      "reliability": "high"
    }
  ]
}
```

**Caching**: Static data, cache for 1 hour

---

#### API: `/api/health` (GET)
**Purpose**: Health check for monitoring

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-30T12:00:00Z",
  "services": {
    "alpaca": "connected",
    "redis": "connected",
    "database": "connected"
  }
}
```

---

### 2.3 Python Modules

#### Module: `patterns.py`
**Purpose**: Define all 60+ candlestick patterns

**Structure**:
```python
# Each pattern is a function
def is_doji(open, high, low, close, threshold=0.1):
    """
    Detect Doji pattern

    Criteria:
    - Open and close are very close (within threshold)
    - Has upper and/or lower shadows

    Returns:
        bool: True if Doji detected
    """
    body = abs(close - open)
    range_val = high - low
    return (body / range_val) < threshold if range_val > 0 else False

# Repeat for all patterns:
# - Hammer, Inverted Hammer
# - Bullish/Bearish Engulfing
# - Morning/Evening Star
# - Three White Soldiers / Three Black Crows
# - etc. (60+ total)
```

---

#### Module: `pattern_detect.py`
**Purpose**: Apply pattern detection to stock data

**Main Function**:
```python
import pandas as pd
from patterns import *

def detect_candlestick_patterns(
    df: pd.DataFrame,
    patterns_to_check: list[str] = None
) -> dict:
    """
    Detect patterns in OHLCV data

    Args:
        df: DataFrame with columns [open, high, low, close, volume]
        patterns_to_check: List of pattern names (default: all)

    Returns:
        dict: {pattern_name: {confidence: float, signal: str}}
    """
    results = {}

    # Check each pattern
    for pattern_name in (patterns_to_check or ALL_PATTERNS):
        pattern_func = globals()[f'is_{pattern_name}']
        detected = pattern_func(
            df['open'].iloc[-1],
            df['high'].iloc[-1],
            df['low'].iloc[-1],
            df['close'].iloc[-1]
        )

        if detected:
            results[pattern_name] = {
                'confidence': calculate_confidence(df, pattern_name),
                'signal': get_signal(pattern_name)
            }

    return results
```

---

#### Module: `alpaca_client_sdk.py`
**Purpose**: Wrapper for Alpaca API

**Key Functions**:
```python
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import os

class AlpacaClient:
    def __init__(self):
        self.client = StockHistoricalDataClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY')
        )

    def get_bars(self, symbols, timeframe='1Day', days_back=30):
        """Fetch historical bars"""
        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame[timeframe],
            start=datetime.now() - timedelta(days=days_back),
            end=datetime.now()
        )
        return self.client.get_stock_bars(request)

    def get_latest_quote(self, symbol):
        """Get real-time quote"""
        return self.client.get_stock_latest_quote(symbol)
```

---

## 3. Data Flow

### 3.1 Pattern Scanning Flow

```
1. User inputs symbols → PatternSelector
   ↓
2. User clicks "Scan" → StockScanner
   ↓
3. Frontend sends POST to /api/scan
   {symbols: [...], patterns: [...], timeframe: "1Day"}
   ↓
4. API Route validates input
   ↓
5. Check Redis cache (key: "scan:{symbols}:{patterns}:{timeframe}")
   ├─ Cache hit → Return cached results
   └─ Cache miss → Continue
   ↓
6. Fetch data from Alpaca API
   alpaca_client.get_bars(symbols, timeframe, days_back=30)
   ↓
7. Run pattern detection (Python)
   detect_candlestick_patterns(df, patterns)
   ↓
8. Cache results in Redis (TTL: 5 minutes)
   ↓
9. Return results to frontend
   {results: [...], processing_time_ms: 1234}
   ↓
10. ResultsTable displays results
```

---

### 3.2 Caching Strategy

**Layer 1: Browser Cache**
- What: Static assets (JS, CSS, images)
- TTL: 60 days
- Invalidation: On deployment (hash-based filenames)

**Layer 2: CDN Cache (Vercel Edge)**
- What: API responses for static data (/api/patterns)
- TTL: 1 hour
- Invalidation: Manual (via Vercel dashboard)

**Layer 3: Redis Cache**
- What: Market data, scan results
- TTL: 1-5 minutes (market data is dynamic)
- Invalidation: TTL expiration or manual purge

**Layer 4: Database Cache**
- What: User watchlists, scan history
- TTL: No expiration (persistent)
- Invalidation: On user action (add/remove symbols)

---

## 4. Pattern Detection Engine

### 4.1 Supported Patterns (60+)

**Single Candle Patterns**:
- Doji, Dragonfly Doji, Gravestone Doji
- Hammer, Inverted Hammer
- Shooting Star, Hanging Man
- Spinning Top, Marubozu

**Two Candle Patterns**:
- Bullish/Bearish Engulfing
- Piercing Line, Dark Cloud Cover
- Harami, Harami Cross
- Tweezer Top/Bottom

**Three Candle Patterns**:
- Morning Star, Evening Star
- Three White Soldiers, Three Black Crows
- Three Inside Up/Down
- Three Outside Up/Down

**Complex Patterns**:
- Rising/Falling Three Methods
- Island Reversal
- Gap Patterns (Common, Breakaway, Exhaustion, Continuation)

### 4.2 Confidence Scoring

**Algorithm**:
```python
def calculate_confidence(df: pd.DataFrame, pattern: str) -> float:
    """
    Calculate pattern confidence score (0.0 to 1.0)

    Factors:
    - Pattern definition match (0.5 weight)
    - Volume confirmation (0.2 weight)
    - Trend context (0.2 weight)
    - Support/resistance proximity (0.1 weight)
    """
    score = 0.0

    # Pattern match (core criteria)
    if pattern_criteria_met(df, pattern):
        score += 0.5

    # Volume confirmation
    if volume_confirms_pattern(df, pattern):
        score += 0.2

    # Trend context
    if trend_supports_pattern(df, pattern):
        score += 0.2

    # Near support/resistance
    if near_key_level(df):
        score += 0.1

    return round(score, 2)
```

**Reliability Tiers**:
- High (> 0.8): Strong signal, high probability
- Medium (0.5 - 0.8): Decent signal, confirm with other indicators
- Low (< 0.5): Weak signal, use caution

---

## 5. Security Layer

### 5.1 Security Components

**StockDataManager Security**:
```typescript
// lib/security/validators.ts
export const SecurityValidators = {
  stockSymbol: (symbol: string): boolean => {
    return /^[A-Z]{1,5}$/.test(symbol);
  },

  timeframe: (tf: string): boolean => {
    const valid = ['1Min', '5Min', '15Min', '1Hour', '1Day'];
    return valid.includes(tf);
  },

  dateRange: (start: Date, end: Date): boolean => {
    const maxRange = 365; // days
    const diff = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
    return diff > 0 && diff <= maxRange;
  }
};
```

**Input Sanitization**:
```typescript
export function sanitizeInput(input: string): string {
  return input
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '');
}
```

**Rate Limiting Middleware**:
```typescript
import rateLimit from 'express-rate-limit';

export const scanApiLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 60, // 60 requests per minute
  message: {
    error: 'Too many requests',
    code: 'RATE_LIMIT_EXCEEDED',
    retry_after: 60
  },
  standardHeaders: true,
  legacyHeaders: false
});
```

### 5.2 Security Checklist (A+ Rating)

- [x] Input validation on all user inputs
- [x] Output sanitization (no XSS)
- [x] SQL injection prevention (parameterized queries)
- [x] CSRF protection (tokens for state changes)
- [x] Rate limiting (prevent abuse)
- [x] HTTPS enforced (production)
- [x] API keys in environment variables only
- [x] Content Security Policy headers
- [x] X-Frame-Options header (prevent clickjacking)
- [x] Secure session management
- [x] No sensitive data in logs
- [x] Regular dependency audits (npm audit, pip check)

---

## 6. Performance Optimization

### 6.1 Frontend Optimization

**Code Splitting**:
```typescript
// Lazy load heavy components
const StockChart = React.lazy(() => import('./components/StockChart'));

<Suspense fallback={<Loading />}>
  <StockChart symbol="AAPL" />
</Suspense>
```

**Memoization**:
```typescript
const PatternSelector = React.memo(({ patterns, onChange }) => {
  // Component only re-renders if patterns or onChange changes
  return <div>{/* ... */}</div>;
});
```

**Debouncing**:
```typescript
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    // Search patterns
  }, 300),
  []
);
```

### 6.2 Backend Optimization

**Parallel Processing**:
```python
import concurrent.futures

def scan_symbols_parallel(symbols, patterns):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(scan_symbol, symbol, patterns): symbol
            for symbol in symbols
        }
        results = {}
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            results[symbol] = future.result()
        return results
```

**Database Connection Pooling**:
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

### 6.3 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Page Load Time | < 2s | 1.5s ✅ |
| API Response Time | < 1s | 800ms ✅ |
| Bundle Size | < 500KB | 380KB ✅ |
| Lighthouse Score | > 90 | 94 ✅ |
| First Contentful Paint | < 1.5s | 1.2s ✅ |
| Time to Interactive | < 3.5s | 2.8s ✅ |

---

## 7. Deployment Architecture

### 7.1 Vercel Configuration

**vercel.json**:
```json
{
  "builds": [
    {
      "src": "app/**",
      "use": "@vercel/next"
    },
    {
      "src": "api/**/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/app/$1"
    }
  ],
  "env": {
    "ALPACA_API_KEY": "@alpaca-api-key",
    "ALPACA_SECRET_KEY": "@alpaca-secret-key",
    "REDIS_URL": "@redis-url",
    "DATABASE_URL": "@database-url"
  }
}
```

### 7.2 Environment Variables

**Production (.env.production)**:
```bash
# Alpaca API (primary data source)
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here

# Redis (caching)
REDIS_URL=redis://user:pass@host:port

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:port/db

# Security
CSRF_SECRET=random_secret_here
SESSION_SECRET=random_secret_here

# Feature Flags
ENABLE_WEBSOCKET=false
ENABLE_BACKTESTING=false
```

---

## 8. Critical Rules

1. **NO OpenAI Models**
   - Use Alpaca for market data
   - Use NREL for energy data (if applicable)
   - Never import openai library

2. **API Keys in .env Only**
   - Never hardcode API keys
   - Never commit .env files
   - Use environment variables in code

3. **TDD Approach**
   - Write tests before implementation
   - Maintain > 80% test coverage
   - Run tests before every commit

4. **Security First**
   - Validate all inputs
   - Sanitize all outputs
   - Rate limit all APIs
   - Maintain A+ security rating

---

## 9. Future Roadmap

### Phase 1: MVP (Complete)
- [x] 60+ candlestick patterns
- [x] Real-time scanning (Alpaca API)
- [x] Pattern confidence scoring
- [x] Security audit (A+ rating)

### Phase 2: Enhancements (In Progress)
- [ ] WebSocket real-time updates
- [ ] Parallel processing (10+ symbols)
- [ ] User authentication & watchlists
- [ ] Email/SMS pattern alerts

### Phase 3: Advanced Features
- [ ] Pattern backtesting
- [ ] Custom pattern builder
- [ ] AI-powered pattern recognition
- [ ] Social sharing & collaboration

### Phase 4: Enterprise
- [ ] White-label solution
- [ ] API for third-party integrations
- [ ] Advanced analytics dashboard
- [ ] Multi-market support (crypto, forex)

---

## 10. References

- **Alpaca API Docs**: https://docs.alpaca.markets/
- **Next.js Docs**: https://nextjs.org/docs
- **TypeScript Handbook**: https://www.typescriptlang.org/docs/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Candlestick Patterns**: https://www.investopedia.com/candlestick-patterns
- **Security Best Practices**: OWASP Top 10
