# CLAUDE.md - Candlestick Screener

## Project Status & Overview

The Candlestick Screener is a **complete React/Next.js transformation** from the original Flask implementation. This AI/ML application scans stocks using **60+ technical candlestick patterns** with real-time data integration.

**Current Status:**
- ✅ **71 Tests Passing** - Professional TDD standards
- ✅ **Security Audit Complete** - A- grade (85/100)
- ✅ **DevOps Assessment Complete** - Critical blockers resolved
- ✅ **Agent Team Validated** - Full workflow validation

## Technology Stack

### Core Dependencies
- **Python 3.8+** - Primary language for pattern detection
- **pandas & numpy** - Data manipulation and numerical computing
- **yfinance** - Real-time stock data (fallback)
- **pandas-ta** - Technical analysis and 60+ candlestick patterns
- **requests** - API communication

### Frontend (React/Next.js)
- **Next.js 14** - React framework with TypeScript
- **Tailwind CSS** - Styling and responsive design
- **Jest & React Testing Library** - Testing framework

## Development Workflow

### Prerequisites
```bash
# Install Python dependencies
pip install pandas numpy yfinance pandas-ta requests

# For frontend development
npm install  # or yarn install
```

### Running the Application

**Development Mode:**
```bash
# Start Next.js development server
npm run dev

# Run Python pattern detection (if separate server)
python patterns.py
```

**Testing:**
```bash
# Run all tests (71 tests)
npm test

# Run tests with coverage
npm run test:coverage

# Run specific test files
npm test -- patterns.test.js
```

**Building for Production:**
```bash
# Build Next.js application
npm run build

# Start production server
npm start
```

## Environment Variables

Create a `.env.local` file in the project root:

```env
# Alpaca API Configuration
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_API_SECRET=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Application Settings
NODE_ENV=development
NEXT_PUBLIC_API_URL=/api

# Fallback Settings
USE_YFINANCE_FALLBACK=true
```

## Key Files & Their Purposes

### Core Pattern Detection
- `patterns.py` - Main candlestick pattern detection engine using pandas-ta
- `data_fetcher.py` - Handles Alpaca API and yfinance data retrieval
- `symbols.py` - Stock symbol management and dataset handling

### Frontend Architecture
- `pages/` - Next.js page components (App Router)
- `components/` - React components for UI
- `lib/` - Utility functions and API clients
- `styles/` - Tailwind CSS and custom styling
- `tests/` - Jest test files with React Testing Library

### Configuration
- `next.config.js` - Next.js configuration
- `tailwind.config.js` - Tailwind CSS setup
- `jest.config.js` - Testing configuration

## Testing Approach

### Test Structure
- **71 Total Tests** covering all critical paths
- **Unit Tests** - Individual pattern detection functions
- **Integration Tests** - API endpoints and data flow
- **Component Tests** - React UI components
- **End-to-End Tests** - Critical user workflows

### Testing Commands
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage

# Run specific test pattern
npm test -- --testNamePattern="candlestick"
```

## Deployment Strategy

### Vercel Deployment (Primary)
```bash
# Deploy to Vercel
npm run build
vercel --prod
```

### Serverless Functions
- Python API endpoints deployed as serverless functions
- Automatic scaling with Vercel's infrastructure
- Edge caching for performance optimization

### Pre-deployment Checklist
1. ✅ All 71 tests passing
2. ✅ Security audit completed (A- grade)
3. ✅ Build optimization verified
4. ✅ Environment variables configured
5. ✅ API rate limits configured

## Coding Standards

### Python Standards
```python
# Pattern detection functions should follow:
def detect_bullish_engulfing(df: pd.DataFrame) -> pd.Series:
    """Detect bullish engulfing pattern with clear docstrings."""
    return pandas_ta.cdl_pattern(df, "engulfing")
```

### React/TypeScript Standards
```typescript
// Components should be typed and functional
interface CandlestickProps {
  data: StockData[];
  pattern: string;
}

const CandlestickChart: React.FC<CandlestickProps> = ({ data, pattern }) => {
  // Implementation
};
```

### File Organization
- **Python files**: snake_case naming (`pattern_detector.py`)
- **React components**: PascalCase naming (`CandlestickChart.tsx`)
- **Test files**: Same name as source + `.test.js` (`patterns.test.js`)

## Common Tasks & Commands

### Development Tasks
```bash
# Start development environment
npm run dev

# Run pattern detection locally
python -m patterns --symbol AAPL --period 1mo

# Test specific stock pattern
python -c "from patterns import scan_symbol; print(scan_symbol('AAPL'))"
```

### Data Management
```bash
# Update stock symbols dataset
python symbols.py --update

# Test data fetching
python data_fetcher.py --symbol AAPL --test
```

### Maintenance Tasks
```bash
# Update dependencies
npm update
pip install --upgrade pandas-ta yfinance

# Security audit
npm audit
pip check
```

## Troubleshooting Tips

### Common Issues

**Data Fetching Failures:**
```bash
# Check Alpaca API status
curl -X GET "https://paper-api.alpaca.markets/v2/clock"

# Test yfinance fallback
python -c "import yfinance as yf; print(yf.download('AAPL', period='1mo'))"
```

**Pattern Detection Issues:**
```python
# Debug specific pattern
from patterns import debug_pattern
debug_pattern('AAPL', 'doji')
```

**Build Failures:**
```bash
# Clear Next.js cache
rm -rf .next
npm run build

# Check TypeScript issues
npm run type-check
```

### Performance Optimization

**For Large Symbol Scans:**
```python
# Use batch processing for multiple symbols
from patterns import batch_scan
results = batch_scan(['AAPL', 'TSLA', 'GOOGL'], workers=4)
```

**Memory Management:**
```python
# Clear DataFrame memory
import gc
del large_dataframe
gc.collect()
```

### API Rate Limiting
- Alpaca API: 200 requests per minute
- yfinance: No official limits, but be respectful
- Implement retry logic with exponential backoff

## Support & Resources

- **Pattern Reference**: Check pandas-ta documentation for 60+ supported patterns
- **Data Sources**: Alpaca API documentation + yfinance GitHub
- **Testing**: Jest and React Testing Library documentation
- **Deployment**: Vercel deployment guide for Next.js applications

This CLAUDE.md provides comprehensive guidance for developing, testing, and maintaining the Candlestick Screener project. Always refer to the latest README for the most current project status and requirements.