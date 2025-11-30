```markdown
# Candlestick Screener - Project Context

## Project Information
- **Project Name**: candlestick-screener
- **Last Updated**: 2025-10-31T13:01:19.251776
- **Language**: Python (with React/Next.js frontend)
- **Framework**: Next.js 14 (frontend), Serverless Functions (backend)
- **Type**: AI/ML Financial Analysis Tool

## Current Sprint & Focus Areas
- **Primary Focus**: Production Deployment & Optimization
- **Secondary Focus**: Feature Enhancement & Performance Tuning
- **Quality Assurance**: Maintaining 71-test coverage and A- security rating

## Architecture Overview
```
Modern Full-Stack Financial Application:
├── Frontend: React/Next.js 14 with TypeScript & Tailwind CSS
├── Backend: Python Serverless API Functions
├── Data: Alpaca API + yfinance fallback
└── Analysis: pandas-ta pattern detection engine (60+ patterns)
```

## Project Description
Candlestick Screener is a sophisticated financial analysis platform that automatically scans and identifies technical candlestick patterns across stock markets. The application leverages machine learning and technical analysis to detect over 60 distinct candlestick formations in real-time, providing traders and investors with actionable market insights.

The system combines modern web technologies with robust financial data processing, featuring a responsive React-based interface backed by Python-powered pattern recognition algorithms. It represents a complete transformation from legacy Flask architecture to a cutting-edge serverless deployment model with enterprise-grade security and testing standards.

## Recent Changes
- **Complete Architecture Migration**: Successfully transformed from Flask to React/Next.js
- **Testing Infrastructure**: Implemented comprehensive test suite with 71 passing tests
- **Security Hardening**: Achieved A- security rating (85/100) through thorough audit
- **DevOps Optimization**: Resolved critical deployment blockers for production readiness
- **Agent Team Validation**: Full workflow validation by specialized testing agents

## Current Blockers
- **None Identified**: All critical deployment blockers have been resolved
- **Ready for Production**: Security audit complete, tests passing, DevOps assessment finalized

## Next Steps & Action Items
1. **Production Deployment** - Deploy to Vercel and validate serverless function performance
2. **Real-time Data Optimization** - Implement WebSocket connections for live market data streaming
3. **Pattern Accuracy Enhancement** - Add backtesting capabilities for pattern success rate analysis
4. **User Authentication** - Implement secure user accounts for personalized watchlists
5. **Mobile App Development** - Explore React Native implementation for native mobile experience

## Development Workflow
### Testing Standards
- 71 comprehensive tests using Jest and React Testing Library
- TDD approach with integration testing coverage
- Security testing integrated into CI/CD pipeline

### Deployment Process
1. Feature development with branch protection
2. Automated testing on pull requests
3. Security audit and performance validation
4. Serverless deployment to Vercel
5. Post-deployment monitoring and analytics

### Code Quality
- TypeScript implementation for type safety
- ESLint and Prettier configuration
- Automated security scanning
- Performance benchmarking

## Notes
- **Pattern Library**: Currently supports 60+ candlestick patterns via pandas-ta
- **Data Sources**: Primary Alpaca API with yfinance fallback for redundancy
- **Performance**: Optimized for high-frequency data processing and real-time analysis
- **Scalability**: Serverless architecture designed for elastic scaling during market hours
- **Compliance**: OWASP security standards implemented for financial data handling

**Maintenance Window**: Consider market hours for deployments (prefer weekends or after-hours)
```