# candlestick-screener

**Branch**: main | **Updated**: 2025-11-30

## Status
Modern React/Next.js 14 application with TypeScript for candlestick pattern screening. Professional frontend with Python serverless APIs, optimized for Vercel deployment. Security Rating: A+

## Today's Focus
1. [ ] Test Alpaca API integration
2. [ ] Review pattern detection accuracy
3. [ ] Performance testing on Vercel

## Done (This Session)
- (none yet)

## Critical Rules
- **NO OpenAI models** - Use DeepSeek, Qwen, Moonshot via OpenRouter
- API keys in `.env` only, never hardcoded
- TDD approach - 59 tests across integration, unit, API, security
- Security-first development (A+ rating)

## Blockers
(none)

## Quick Commands
```bash
# Development
npm run dev

# Build for production
npm run build

# Run tests
pytest                          # Backend tests
npm test                        # Frontend tests

# Security validation
python verify-deployment.py

# Test Alpaca integration
python quick_test.py

# Deploy to Vercel
vercel --prod
```

## Tech Stack
- **Frontend**: React 18, Next.js 14.2.5, TypeScript 5.8.3
- **Styling**: Tailwind CSS 3.4.6, Heroicons 2.2.0
- **Backend**: Python serverless functions (Vercel)
- **Market Data**: Alpaca API (primary), yfinance (fallback)
- **Pattern Analysis**: pandas-ta (60+ candlestick patterns)
- **Database**: Neon PostgreSQL
- **Security**: CSRF protection, rate limiting, input validation
- **Testing**: Jest 29.7.0, pytest, Testing Library
- **Deployment**: Vercel serverless platform
