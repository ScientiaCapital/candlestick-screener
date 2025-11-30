# Validate - Multi-Phase Validation Workflow

Execute comprehensive validation across frontend, backend, and security layers.

## Critical Rules (Pre-Validation Checklist)

- [ ] NO OpenAI models anywhere in codebase
- [ ] All API keys in .env files only (never hardcoded)
- [ ] TDD approach: tests written before implementation
- [ ] Alpaca API for market data (primary), yfinance (fallback only)

---

## Validation Phases

### Phase 1: Frontend Lint + TypeScript Type Check
```bash
cd /Users/tmkipper/Desktop/tk_projects/candlestick-screener
npm run lint
npx tsc --noEmit
```

**Success Criteria**:
- Zero ESLint errors
- Zero TypeScript type errors
- No unused imports or variables
- Tailwind class names valid

**Common Fixes**:
- Add `// eslint-disable-next-line` only if justified
- Fix type errors with proper interfaces/types
- Remove unused imports automatically: `npm run lint -- --fix`

---

### Phase 2: Frontend Build
```bash
npm run build
```

**Success Criteria**:
- Build completes without errors
- Bundle size < 500KB (excluding chunks)
- No hydration errors
- Static optimization enabled for pages

**Performance Checks**:
- Lighthouse score > 90 (run `npm run lighthouse`)
- First Contentful Paint < 1.5s
- Time to Interactive < 3.5s

---

### Phase 3: Frontend Tests
```bash
npm test -- --coverage
```

**Success Criteria**:
- All tests pass
- Coverage > 80% (statements, branches, functions, lines)
- No skipped tests (`.skip()` not allowed in main branch)
- Snapshot tests up-to-date

**Critical Test Areas**:
- PatternSelector component (user interactions)
- StockScanner logic (API integration)
- ResultsTable rendering (data display)
- Error boundary behavior

---

### Phase 4: Backend Tests
```bash
pytest --cov=. --cov-report=term-missing -v
```

**Success Criteria**:
- All tests pass
- Coverage > 85%
- No warnings about deprecated functions
- All candlestick patterns tested

**Critical Test Areas**:
- `patterns.py` - All 60+ pattern functions
- `alpaca_client_sdk.py` - API error handling
- `pattern_detect.py` - Detection accuracy
- Serverless API routes (`/api/*`)

---

### Phase 5: Security Check
```bash
python verify-deployment.py
```

**Success Criteria**:
- Security rating: A or A+
- No SQL injection vulnerabilities
- CSRF protection enabled
- Rate limiting functional
- Input validation on all endpoints

**Security Audit Points**:
- [ ] API keys never exposed to frontend
- [ ] User input sanitized (stock symbols, dates)
- [ ] Content Security Policy headers set
- [ ] HTTPS enforced in production
- [ ] No XSS vulnerabilities

---

### Phase 6: Alpaca Integration Test
```bash
python quick_test.py
```

**Success Criteria**:
- Alpaca API connection successful
- Market data fetch < 2s for 5 symbols
- Pattern detection runs without errors
- WebSocket connection stable (if enabled)

**Test Scenarios**:
- Valid symbol (e.g., AAPL, TSLA)
- Invalid symbol (graceful error handling)
- Market closed (fallback to latest available data)
- API rate limit handling

---

## Full Validation Command
```bash
# Run all phases sequentially
npm run lint && \
npx tsc --noEmit && \
npm run build && \
npm test -- --coverage && \
pytest --cov=. --cov-report=term-missing -v && \
python verify-deployment.py && \
python quick_test.py
```

---

## Post-Validation Checklist

- [ ] All 6 phases passed
- [ ] Git status clean (no uncommitted changes)
- [ ] CLAUDE.md updated if architecture changed
- [ ] Security audit report reviewed (if Phase 5 flagged issues)
- [ ] Ready for deployment to Vercel

---

## Troubleshooting

### Phase 1 Fails (Lint/Types)
- Run `npm run lint -- --fix` to auto-fix
- Check TypeScript version matches package.json
- Verify Tailwind config matches usage

### Phase 2 Fails (Build)
- Clear `.next` cache: `rm -rf .next`
- Check Node version: `node -v` (should be 18+)
- Review build errors in terminal output

### Phase 3/4 Fails (Tests)
- Run single test file: `npm test -- <filename>`
- Update snapshots: `npm test -- -u`
- Check test environment variables set

### Phase 5 Fails (Security)
- Review `COMPREHENSIVE_SECURITY_AUDIT_REPORT.md`
- Fix critical issues before proceeding
- Re-run audit after fixes

### Phase 6 Fails (Alpaca)
- Verify `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in `.env`
- Check API quota: visit Alpaca dashboard
- Test with single symbol first

---

## CI/CD Integration

This validation workflow should run automatically on:
- Every commit to main branch
- Pull request creation
- Pre-deployment (Vercel build)

**GitHub Actions Example**:
```yaml
name: Validate
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit
      - run: npm run build
      - run: npm test -- --coverage
      - run: pytest --cov=.
      - run: python verify-deployment.py
```
