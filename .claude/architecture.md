# Candlestick Screener Architecture

## 1. Technology Stack

### Frontend
- **React 18+** with TypeScript
- **Next.js 14** - App Router, Server Components, API Routes
- **Tailwind CSS** - Utility-first styling system
- **Jest** + **React Testing Library** - Testing framework
- **Vercel** - Deployment platform

### Backend/Data Processing
- **Python 3.8+** - Core programming language
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing
- **pandas-ta** - Technical analysis library (60+ candlestick patterns)
- **yfinance** - Yahoo Finance API wrapper (fallback data source)
- **alpaca-py** - Alpaca Markets API client (primary data source)
- **requests** - HTTP client for API calls

### Infrastructure & Security
- **python-dotenv** - Environment variable management
- **cryptography** - Encryption and security utilities
- **setuptools** - Python package distribution

## 2. Design Patterns

### Frontend Patterns
- **Component-Based Architecture** - Modular React components with TypeScript interfaces
- **Server-Side Rendering (SSR)** - Next.js App Router for optimal performance
- **Custom Hooks** - Reusable stateful logic for data fetching and pattern management
- **Context API** - Global state management for user preferences and market data

### Backend Patterns
- **Strategy Pattern** - Multiple data source providers (Alpaca primary, yfinance fallback)
- **Factory Pattern** - Pattern detection engine generating different candlestick analyzers
- **Repository Pattern** - Abstracted data access layer for stock data sources
- **Observer Pattern** - Real-time data updates and WebSocket connections

### API Patterns
- **RESTful API** - Next.js API routes for serverless functions
- **Adapter Pattern** - Unified interface for multiple financial data providers
- **Circuit Breaker** - Fallback mechanisms when primary APIs fail

## 3. Key Components

### Frontend Components
```
src/
├── app/                    # Next.js 14 App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Main dashboard
│   └── api/               # Serverless API routes
├── components/
│   ├── ui/                # Reusable UI components
│   ├── charts/            # Candlestick chart components
│   ├── screener/          # Pattern screening interface
│   └── symbols/           # Symbol search and management
├── hooks/
│   ├── usePatterns.ts     # Pattern detection logic
│   ├── useMarketData.ts   # Real-time data fetching
│   └── useWebSocket.ts    # Live updates
└── lib/
    ├── patterns.ts        # Pattern definitions and mappings
    └── alpaca-client.ts   # Financial API client
```

### Backend Components
```
python/
├── pattern_engine/
│   ├── __init__.py
│   ├── detector.py        # Main pattern detection engine
│   ├── patterns/          # Individual pattern implementations
│   └── validators.py      # Pattern validation logic
├── data_sources/
│   ├── base.py            # Abstract data source
│   ├── alpaca.py          # Alpaca API implementation
│   ├── yfinance.py        # Yahoo Finance fallback
│   └── cache.py           # Data caching layer
├── api/
│   ├── routes.py          # FastAPI/Flask route definitions
│   └── middleware.py      # Auth and rate limiting
└── models/
    ├── schemas.py         # Pydantic models
    └── database.py        # Data models (if applicable)
```

## 4. Data Flow

### Pattern Screening Workflow
1. **User Input** → User selects symbols, timeframes, and pattern filters
2. **Symbol Resolution** → Frontend validates and normalizes symbol list
3. **Data Fetching** → 
   - Primary: Alpaca API (real-time/market hours)
   - Fallback: yfinance (extended hours/historical)
4. **Pattern Detection** → pandas-ta processes OHLCV data through 60+ pattern functions
5. **Result Aggregation** → Patterns ranked by strength and reliability
6. **UI Rendering** → Results displayed in sortable, filterable table with visual indicators

### Real-time Updates Flow
```
Alpaca WebSocket → Message Queue → Pattern Engine → UI Update
     ↓
Data Validation → Cache Update → Broadcast to Connected Clients
```

### Batch Processing Flow
```python
# Pseudocode for batch screening
def screen_symbols(symbols: List[str], patterns: List[str]) -> Dict:
    results = {}
    for symbol in symbols:
        data = data_source.get_ohlcv(symbol, timeframe="1d")
        pattern_results = pattern_engine.detect_all(data, patterns)
        results[symbol] = {
            'patterns': pattern_results,
            'metadata': data.metadata,
            'confidence': calculate_confidence(pattern_results)
        }
    return rank_results(results)
```

## 5. External Dependencies

### Primary APIs
- **Alpaca Markets API** - Real-time and historical market data
- **Yahoo Finance API** (via yfinance) - Fallback data source

### Python Dependencies
```python
# Core Data Processing
pandas>=1.5.0        # Data manipulation and analysis
numpy>=1.21.0        # Numerical computations
pandas-ta>=0.3.0     # Technical analysis patterns

# API Clients
alpaca-py>=0.18.0    # Alpaca Trading API
yfinance>=0.2.0      # Yahoo Finance wrapper
requests>=2.28.0     # HTTP requests

# Security & Configuration
python-dotenv>=1.0.0 # Environment management
cryptography>=41.0.0 # Security utilities
```

## 6. API Design

### Next.js API Routes
```typescript
// app/api/patterns/route.ts
export async function POST(request: Request) {
  const { symbols, patterns, timeframe } = await request.json();
  
  // Serverless function calls Python backend
  const results = await analyzePatterns(symbols, patterns, timeframe);
  
  return Response.json(results);
}

// app/api/symbols/search/route.ts
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');
  
  const symbols = await searchSymbols(query);
  return Response.json(symbols);
}
```

### Python Backend API (if separate service)
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ScreeningRequest(BaseModel):
    symbols: List[str]
    patterns: List[str]
    timeframe: str = "1d"

@app.post("/api/screen")
async def screen_patterns(request: ScreeningRequest):
    try:
        results = pattern_engine.batch_screen(
            request.symbols, 
            request.patterns, 
            request.timeframe
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 7. Data Schema

### Pattern Detection Results
```python
@dataclass
class PatternResult:
    symbol: str
    pattern_name: str
    detected: bool
    strength: float  # 0.0 - 1.0
    timestamp: datetime
    metadata: Dict[str, Any]
    
@dataclass
class ScreeningResult:
    symbol: str
    patterns: List[PatternResult]
    overall_confidence: float
    price_data: pd.DataFrame
    last_updated: datetime
```

### Market Data Schema
```python
# OHLCV Data Structure
OHLCV = TypedDict('OHLCV', {
    'open': float,
    'high': float, 
    'low': float,
    'close': float,
    'volume': float,
    'timestamp': datetime
})
```

## 8. Security Considerations

### API Security
- **API Key Management** - Environment variables with encryption
- **Rate Limiting** - Request throttling per user/IP
- **Input Validation** - Symbol sanitization and pattern whitelisting
- **CORS Configuration** - Restricted to trusted domains

### Data Security
- **SSL/TLS** - All external API calls over HTTPS
- **Data Sanitization** - Input validation for all user-provided symbols
- **Credential Encryption** - cryptography library for sensitive data

### Application Security
- **XSS Prevention** - React's built-in XSS protection
- **CSRF Protection** - Next.js anti-CSRF tokens
- **Content Security Policy** - Strict CSP headers in production

## 9. Performance Optimization

### Frontend Optimizations
- **Static Generation** - Next.js SSG for pattern documentation
- **Dynamic Imports** - Code splitting for heavy charting libraries
- **Image Optimization** - Next.js Image component with lazy loading
- **Client-side Caching** - React Query for API response caching

### Backend Optimizations
```python
# Data caching strategy
class DataCache:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.ttl = 300  # 5 minutes
    
    async def get_ohlcv(self, symbol: str, timeframe: str):
        cache_key = f"{symbol}:{timeframe}"
        cached = await self.redis_client.get(cache_key)
        if cached:
            return pickle.loads(cached)
        
        # Fetch from API and cache
        data = await self.data_source.fetch(symbol, timeframe)
        await self.redis_client.setex(cache_key, self.ttl, pickle.dumps(data))
        return data
```

### Pattern Detection Optimization
- **Vectorized Operations** - pandas/numpy for batch processing
- **Parallel Processing** - asyncio for concurrent API calls
- **Pattern Caching** - Memoization of pattern detection results

## 10. Deployment Strategy

### Vercel Deployment (Primary)
```yaml
# vercel.json
{
  "version": 2,
  "builds": [
    { "src": "package.json", "use": "@vercel/next" },
    { "src": "python/api/**/*.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/python/api/$1" },
    { "src": "/(.*)", "dest": "/index.html" }
  ],
  "env": {
    "ALPACA_API_KEY": "@alpaca-api-key",
    "ALPACA_SECRET_KEY": "@alpaca-secret-key"
  }
}
```

### Development Deployment
```bash
# Local development
npm run dev          # Frontend development
python -m uvicorn api.main:app --reload  # Backend API

# Production build
npm run build       # Next.js production build
npm start          # Start production server
```

### Monitoring & Observability
- **Vercel Analytics** - Performance monitoring
- **Custom Metrics** - Pattern detection success rates
- **Error Tracking** - Sentry integration for frontend/backend
- **API Health Checks** - Regular monitoring of external APIs

This architecture supports high-performance candlestick pattern screening with production-grade security, scalability, and maintainability while leveraging modern React/Next.js and Python data processing capabilities.