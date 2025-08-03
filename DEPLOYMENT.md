# Candlestick Screener - Vercel Deployment Guide

## Overview
This guide covers deploying the candlestick screener Flask application to Vercel with Alpaca integration and Neon database support.

## Prerequisites
- Vercel account
- Alpaca account (paper trading credentials)
- Neon database instance
- GitHub repository (for automatic deployments)

## Required Environment Variables

Set these environment variables in your Vercel project settings:

### Core Application
```
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key-here
```

### Alpaca API Configuration
```
ALPACA_API_KEY=your-alpaca-api-key
ALPACA_SECRET_KEY=your-alpaca-secret-key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets
```

### Database (Neon PostgreSQL)
```
DATABASE_URL=postgresql://user:password@host:port/database
```

### Caching & Rate Limiting (Optional - uses Redis)
```
CACHE_TYPE=simple
CACHE_TIMEOUT=300
RATELIMIT_DEFAULT=200/hour
```

### Security
```
CSRF_SECRET_KEY=your-csrf-secret-key
API_RATE_LIMIT=100/hour
REQUEST_TIMEOUT=30
CORS_ORIGINS=https://your-domain.vercel.app
ALLOWED_HOSTS=your-domain.vercel.app
```

### Performance Settings
```
BATCH_SIZE=10
MAX_SYMBOLS=1000
```

## Deployment Steps

### 1. Repository Setup
1. Push your code to GitHub
2. Connect your GitHub repository to Vercel

### 2. Vercel Configuration
1. Go to your Vercel dashboard
2. Import your GitHub repository
3. Set Framework Preset to "Other"
4. Configure environment variables as listed above

### 3. Build Configuration
The `vercel.json` file is already configured with:
- Python 3.9 runtime
- 50MB lambda size limit
- 30-second timeout
- Optimized for serverless deployment

### 4. Database Setup (Neon)
1. Create a Neon database instance
2. Copy the connection string
3. Set `DATABASE_URL` environment variable in Vercel

### 5. Alpaca API Setup
1. Create Alpaca account (paper trading)
2. Generate API keys
3. Set `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in Vercel

## Serverless Optimizations Applied

### File System Handling
- Fallback to default symbols if CSV file unavailable
- Memory-only caching when no write access
- Conditional logging to files

### Data Management
- Dynamic data fetching from Alpaca API instead of local files
- Limited processing (10 symbols max for demo)
- Efficient caching strategies

### Performance
- 30-second function timeout
- Optimized dependencies
- Memory-efficient pattern analysis

## Testing Deployment

### Health Check Endpoint
```
GET /health
```
Returns system status including:
- Cache connectivity
- Symbol availability
- Alpaca API connection

### Test Endpoints
1. `GET /` - Main application
2. `GET /health` - Health check
3. `GET /stats` - System statistics
4. `POST /snapshot` - Update stock data

## Monitoring & Troubleshooting

### Vercel Function Logs
- Check Vercel dashboard for function logs
- Monitor cold start times
- Watch for timeout issues

### Common Issues
1. **Timeout errors**: Reduce batch size or symbol count
2. **Memory errors**: Optimize pandas operations
3. **API rate limits**: Implement proper retry logic
4. **Database connection**: Check Neon connection string

### Performance Metrics
- Function duration should be < 30 seconds
- Memory usage should be < 1GB
- Cold start time should be < 10 seconds

## Production Considerations

### Security
- All sensitive data in environment variables
- CSRF protection enabled
- Rate limiting configured
- Input validation active

### Scalability
- Stateless design for serverless
- Efficient caching
- Limited concurrent processing

### Cost Optimization
- Function timeout set to 30 seconds
- Efficient API usage
- Memory-optimized operations

## Rollback Strategy
1. Keep previous deployment available
2. Monitor error rates after deployment
3. Use Vercel's instant rollback feature
4. Test in staging environment first

## Support
- Check Vercel documentation for platform issues
- Review Alpaca API documentation for data issues
- Monitor application logs for debugging

## Version Information
- Python: 3.9
- Flask: 2.3.3
- Vercel Runtime: @vercel/python
- Deployment: Serverless optimized