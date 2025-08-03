# Deployment Checklist - Candlestick Screener

## Pre-Deployment Checklist

### 1. Code Preparation
- [ ] All code committed to Git
- [ ] Latest changes pushed to main branch
- [ ] No sensitive data in code (API keys, passwords)
- [ ] Dependencies updated in requirements.txt
- [ ] vercel.json configuration verified

### 2. Configuration Files
- [ ] `vercel.json` exists and configured
- [ ] `requirements.txt` includes all dependencies
- [ ] `app.py` optimized for serverless
- [ ] Environment variables documented

### 3. Environment Setup (Vercel Dashboard)
- [ ] FLASK_ENV=production
- [ ] SECRET_KEY set (secure random string)
- [ ] ALPACA_API_KEY configured
- [ ] ALPACA_SECRET_KEY configured
- [ ] ALPACA_BASE_URL set to paper trading
- [ ] DATABASE_URL configured (Neon)
- [ ] CSRF_SECRET_KEY set
- [ ] Additional security variables set

### 4. External Services
- [ ] Alpaca account active (paper trading)
- [ ] Neon database accessible
- [ ] API credentials tested locally
- [ ] Database connection verified

### 5. Testing
- [ ] Local testing completed
- [ ] Health check endpoint works
- [ ] Pattern analysis functional
- [ ] API endpoints responding
- [ ] Error handling verified

## Deployment Process

### Step 1: Connect Repository
```bash
# Ensure all changes are committed
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### Step 2: Vercel Setup
1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Import from GitHub
4. Select your repository
5. Configure as follows:
   - Framework: Other
   - Root Directory: ./
   - Build Command: (leave empty)
   - Output Directory: (leave empty)

### Step 3: Environment Variables
Copy and paste each variable from the documentation into Vercel settings.

### Step 4: Deploy
Click "Deploy" and wait for build completion.

## Post-Deployment Verification

### 1. Basic Functionality
- [ ] Application loads at Vercel URL
- [ ] No 500 errors on main page
- [ ] Health check returns 200 OK
- [ ] Static assets load correctly

### 2. API Endpoints
- [ ] GET / returns HTML page
- [ ] GET /health returns JSON status
- [ ] GET /stats returns system statistics
- [ ] POST /snapshot works (with proper auth)

### 3. Data Integration
- [ ] Alpaca API connection successful
- [ ] Default symbols load correctly
- [ ] Pattern analysis works
- [ ] Caching functional

### 4. Security
- [ ] HTTPS redirect working
- [ ] CSRF protection active
- [ ] Rate limiting functional
- [ ] No sensitive data exposed

### 5. Performance
- [ ] Page loads in < 5 seconds
- [ ] API responses in < 30 seconds
- [ ] No timeout errors
- [ ] Memory usage reasonable

## Verification Commands

### Test Health Endpoint
```bash
curl https://your-app.vercel.app/health
```
Expected response:
```json
{
  "status": "healthy",
  "cache": "ok",
  "symbols": "ok",
  "alpaca_api": "ok",
  "timestamp": "2024-01-XX..."
}
```

### Test Stats Endpoint
```bash
curl https://your-app.vercel.app/stats
```

### Test Main Application
Visit `https://your-app.vercel.app` in browser and verify:
- Page loads without errors
- Symbols appear in dropdown
- Pattern selection works
- Results display correctly

## Troubleshooting

### Common Issues

#### Build Failures
- Check requirements.txt for invalid versions
- Verify Python 3.9 compatibility
- Check Vercel build logs

#### Runtime Errors
- Check environment variables
- Verify API credentials
- Review function timeout settings

#### Connection Issues
- Test Alpaca API credentials
- Verify Neon database URL
- Check network connectivity

#### Performance Issues
- Monitor function duration
- Check memory usage
- Optimize batch processing

### Debug Commands
```bash
# Check Vercel deployment status
vercel ls

# View function logs
vercel logs [deployment-url]

# Test locally with production config
FLASK_ENV=production python app.py
```

## Rollback Procedure

If deployment fails or issues arise:

1. **Immediate Rollback**
   - Go to Vercel dashboard
   - Find previous working deployment
   - Click "Promote to Production"

2. **Fix and Redeploy**
   - Identify issue from logs
   - Fix in code
   - Test locally
   - Commit and push
   - Vercel auto-deploys

3. **Emergency Measures**
   - Disable problematic features
   - Switch to maintenance mode
   - Notify users if necessary

## Success Criteria

Deployment is successful when:
- [ ] All verification checks pass
- [ ] No critical errors in logs
- [ ] Performance within acceptable limits
- [ ] Security measures functional
- [ ] Users can access all features

## Documentation Updates

After successful deployment:
- [ ] Update README with live URL
- [ ] Document any configuration changes
- [ ] Update API documentation
- [ ] Share access credentials securely

## Monitoring Setup

Post-deployment monitoring:
- [ ] Set up error alerts
- [ ] Monitor performance metrics
- [ ] Track API usage
- [ ] Review security logs

## Next Steps

After successful deployment:
1. Monitor application for 24 hours
2. Gather user feedback
3. Plan feature enhancements
4. Set up automated testing
5. Configure staging environment