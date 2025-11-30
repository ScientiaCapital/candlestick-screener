# Generate PRP - Pseudo-Requirements Document

Generate a comprehensive PRP (Pseudo-Requirements Plan) for new features in the candlestick-screener project.

## Usage
```
/generate-prp <feature_name>
```

Examples:
- `/generate-prp websocket-streaming`
- `/generate-prp user-watchlist`
- `/generate-prp advanced-pattern-filter`

---

## PRP Generation Workflow

### Step 1: Load Project Context

Read the following files to understand current architecture:

1. **Core Documentation**:
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/CLAUDE.md`
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/.claude/CLAUDE.md`
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/PLANNING.md`
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/TASK.md`

2. **Technical References**:
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/patterns.py` - Pattern detection logic
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/alpaca_client_sdk.py` - Alpaca API integration
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/app/page.tsx` - Main React component
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/api/scan/route.ts` - Serverless API example

3. **Security Standards**:
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/COMPREHENSIVE_SECURITY_AUDIT_REPORT.md`
   - `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/verify-deployment.py`

---

### Step 2: Analyze Feature Requirements

**Questions to Answer**:
1. What user problem does this feature solve?
2. What are the technical dependencies (Alpaca API, database, etc.)?
3. How does it integrate with existing components?
4. What are the security implications?
5. What is the performance impact?

**Feature Classification**:
- **Frontend-Only**: UI components, state management
- **Backend-Only**: API routes, data processing
- **Full-Stack**: Frontend + Backend + Database

---

### Step 3: Design Components

#### Frontend Components (React + TypeScript)

**Pattern to Follow**:
```tsx
// Example: PatternSelector.tsx
import React, { useState } from 'react';

interface PatternSelectorProps {
  onPatternsChange: (patterns: string[]) => void;
  availablePatterns: string[];
}

export const PatternSelector: React.FC<PatternSelectorProps> = ({
  onPatternsChange,
  availablePatterns
}) => {
  const [selectedPatterns, setSelectedPatterns] = useState<string[]>([]);

  const handleTogglePattern = (pattern: string) => {
    const updated = selectedPatterns.includes(pattern)
      ? selectedPatterns.filter(p => p !== pattern)
      : [...selectedPatterns, pattern];

    setSelectedPatterns(updated);
    onPatternsChange(updated);
  };

  return (
    <div className="grid grid-cols-3 gap-4 p-4">
      {availablePatterns.map(pattern => (
        <button
          key={pattern}
          onClick={() => handleTogglePattern(pattern)}
          className={`
            px-4 py-2 rounded-lg transition-colors
            ${selectedPatterns.includes(pattern)
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            }
          `}
        >
          {pattern}
        </button>
      ))}
    </div>
  );
};
```

**Component Checklist**:
- [ ] TypeScript interfaces defined
- [ ] Tailwind CSS for styling
- [ ] Responsive design (mobile-first)
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] Error states handled
- [ ] Loading states displayed

---

#### Backend API Routes (Next.js Serverless)

**Pattern to Follow**:
```typescript
// Example: app/api/patterns/detect/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { validateStockSymbol, sanitizeInput } from '@/lib/security';
import { detectPatterns } from '@/lib/patterns';

export async function POST(request: NextRequest) {
  try {
    // 1. Parse and validate input
    const body = await request.json();
    const { symbol, timeframe } = body;

    if (!validateStockSymbol(symbol)) {
      return NextResponse.json(
        { error: 'Invalid stock symbol' },
        { status: 400 }
      );
    }

    // 2. Fetch data from Alpaca
    const marketData = await fetchAlpacaData(sanitizeInput(symbol), timeframe);

    // 3. Detect patterns
    const patterns = await detectPatterns(marketData);

    // 4. Return results
    return NextResponse.json({
      symbol,
      patterns,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Pattern detection error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

**API Route Checklist**:
- [ ] Input validation (never trust client)
- [ ] Input sanitization (prevent injection)
- [ ] Error handling (try/catch)
- [ ] Rate limiting (prevent abuse)
- [ ] Response compression (optimize bandwidth)
- [ ] CORS headers set correctly

---

### Step 4: Alpaca SDK Integration

**Pattern to Follow**:
```python
# Example: alpaca_client_sdk.py enhancement
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

def fetch_bars_with_cache(
    symbols: list[str],
    timeframe: TimeFrame,
    days_back: int = 30,
    cache_ttl: int = 300  # 5 minutes
):
    """
    Fetch stock bars with Redis caching

    Args:
        symbols: List of stock symbols
        timeframe: Alpaca TimeFrame object
        days_back: Number of days of historical data
        cache_ttl: Cache time-to-live in seconds

    Returns:
        dict: {symbol: DataFrame} with OHLCV data
    """
    cache_key = f"bars:{','.join(symbols)}:{timeframe}:{days_back}"

    # Check cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from Alpaca
    client = StockHistoricalDataClient(
        api_key=os.getenv('ALPACA_API_KEY'),
        secret_key=os.getenv('ALPACA_SECRET_KEY')
    )

    request_params = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=timeframe,
        start=datetime.now() - timedelta(days=days_back),
        end=datetime.now()
    )

    bars = client.get_stock_bars(request_params)

    # Cache result
    redis_client.setex(cache_key, cache_ttl, json.dumps(bars))

    return bars
```

**Alpaca Integration Checklist**:
- [ ] API keys from environment variables only
- [ ] Rate limit handling (max 200 req/min)
- [ ] Retry logic with exponential backoff
- [ ] Caching strategy (Redis preferred)
- [ ] Error handling (market closed, invalid symbol)
- [ ] WebSocket for real-time data (optional)

---

### Step 5: Security Measures

**Input Validation**:
```typescript
// lib/security.ts
export function validateStockSymbol(symbol: string): boolean {
  // Only allow A-Z, max 5 characters
  const symbolRegex = /^[A-Z]{1,5}$/;
  return symbolRegex.test(symbol);
}

export function sanitizeInput(input: string): string {
  // Remove special characters
  return input.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
}

export function validateTimeframe(timeframe: string): boolean {
  const validTimeframes = ['1Min', '5Min', '15Min', '1Hour', '1Day'];
  return validTimeframes.includes(timeframe);
}
```

**Security Checklist**:
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (sanitize output)
- [ ] CSRF tokens for state-changing operations
- [ ] Rate limiting per IP address
- [ ] Content Security Policy headers

---

### Step 6: Caching Strategy

**Cache Layers**:
1. **Browser Cache**: Static assets (60 days)
2. **CDN Cache**: API responses (5 minutes)
3. **Redis Cache**: Market data (1-5 minutes)
4. **Database Cache**: Pattern results (1 hour)

**Example Redis Caching**:
```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

export async function getCachedOrFetch<T>(
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

---

### Step 7: Generate PRP Document

**Output Location**: `/Users/tmkipper/Desktop/tk_projects/candlestick-screener/PRPs/<feature_name>_prp.md`

**PRP Template Structure**:
1. Overview (what, why, who)
2. Technical Requirements
3. Component Design (frontend + backend)
4. API Integration (Alpaca)
5. Security Considerations
6. Performance Optimization
7. Testing Strategy
8. Deployment Plan
9. Success Metrics

Use the base template at:
`/Users/tmkipper/Desktop/tk_projects/candlestick-screener/PRPs/templates/prp_base.md`

---

## Example PRPs

### WebSocket Streaming
- Real-time price updates
- Pattern detection on live data
- Auto-refresh scan results

### User Watchlist
- Save favorite symbols to database
- Custom pattern alerts
- Email notifications

### Advanced Pattern Filters
- Combine multiple patterns (AND/OR)
- Confidence score threshold
- Timeframe selection

---

## Critical Rules Reminder

- **NO OpenAI** - Use Alpaca for market data, NREL for energy data
- **API Keys in .env** - Never hardcode, never commit
- **TDD Approach** - Write tests before implementation
- **Security First** - Validate all inputs, sanitize all outputs
- **Serverless Optimization** - Cold start < 200ms, execution < 10s
