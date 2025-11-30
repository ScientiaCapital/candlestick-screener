# Execute PRP - 6-Phase Implementation Workflow

Execute a PRP (Pseudo-Requirements Plan) with security-first, TDD approach.

## Usage
```
/execute-prp <prp_file_path>
```

Example:
```
/execute-prp PRPs/websocket_streaming_prp.md
```

---

## Phase 1: Context Loading

### 1.1 Load PRP Document
```bash
cat /Users/tmkipper/Desktop/tk_projects/candlestick-screener/PRPs/<feature>_prp.md
```

### 1.2 Load Project Context
Read these files to understand current state:
- `CLAUDE.md` - Project overview
- `PLANNING.md` - Architecture
- `TASK.md` - Current status
- `package.json` - Dependencies
- `requirements.txt` - Python dependencies

### 1.3 Verify Prerequisites
- [ ] Node.js 18+ installed
- [ ] Python 3.11+ activated (venv)
- [ ] Alpaca API keys in `.env`
- [ ] Database connection working (if needed)
- [ ] Redis running (if caching required)

**Stop if any prerequisite fails - resolve before continuing.**

---

## Phase 2: ULTRATHINK Planning

### 2.1 Break Down PRP into Tasks

**Task Template**:
```markdown
## Task: <name>
- Type: [Frontend | Backend | Full-Stack | Infrastructure]
- Dependencies: [list tasks that must complete first]
- Estimated Time: [15min | 30min | 1hr | 2hr]
- Files to Modify: [absolute paths]
- Files to Create: [absolute paths]
- Tests Required: [test file paths]
```

**Example Task Breakdown**:
```markdown
## Task 1: Create PatternFilter Component
- Type: Frontend
- Dependencies: None
- Estimated Time: 1hr
- Files to Modify:
  - /Users/tmkipper/Desktop/tk_projects/candlestick-screener/app/page.tsx
- Files to Create:
  - /Users/tmkipper/Desktop/tk_projects/candlestick-screener/app/components/PatternFilter.tsx
  - /Users/tmkipper/Desktop/tk_projects/candlestick-screener/app/components/__tests__/PatternFilter.test.tsx
- Tests Required:
  - Render test
  - User interaction test
  - State management test
```

### 2.2 Security Impact Analysis

**Questions to Answer**:
1. Does this feature accept user input? → Validation required
2. Does it interact with external APIs? → Rate limiting required
3. Does it store data? → Encryption required
4. Does it authenticate users? → Session management required

**Security Checklist**:
- [ ] Input validation implemented
- [ ] Output sanitization implemented
- [ ] Authentication/authorization checked
- [ ] Rate limiting configured
- [ ] Error messages don't leak sensitive info
- [ ] HTTPS enforced in production

### 2.3 Performance Impact Analysis

**Metrics to Consider**:
- Bundle size increase (target: < 50KB per feature)
- API response time (target: < 2s)
- Database query time (target: < 500ms)
- Cache hit rate (target: > 80%)

**Optimization Strategies**:
- Code splitting (React.lazy)
- Data pagination (limit 100 records)
- Debouncing (user input)
- Memoization (expensive calculations)

---

## Phase 3: Implementation (TDD + Security-First)

### 3.1 Write Tests FIRST

**Frontend Test Example**:
```typescript
// PatternFilter.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { PatternFilter } from '../PatternFilter';

describe('PatternFilter', () => {
  it('renders all pattern options', () => {
    const patterns = ['Doji', 'Hammer', 'Engulfing'];
    render(<PatternFilter patterns={patterns} onFilter={jest.fn()} />);

    patterns.forEach(pattern => {
      expect(screen.getByText(pattern)).toBeInTheDocument();
    });
  });

  it('calls onFilter when pattern selected', () => {
    const mockOnFilter = jest.fn();
    render(<PatternFilter patterns={['Doji']} onFilter={mockOnFilter} />);

    fireEvent.click(screen.getByText('Doji'));

    expect(mockOnFilter).toHaveBeenCalledWith(['Doji']);
  });

  it('handles multiple pattern selection', () => {
    const mockOnFilter = jest.fn();
    const patterns = ['Doji', 'Hammer'];
    render(<PatternFilter patterns={patterns} onFilter={mockOnFilter} />);

    fireEvent.click(screen.getByText('Doji'));
    fireEvent.click(screen.getByText('Hammer'));

    expect(mockOnFilter).toHaveBeenLastCalledWith(['Doji', 'Hammer']);
  });
});
```

**Backend Test Example**:
```python
# test_pattern_detection.py
import pytest
from pattern_detect import detect_candlestick_patterns
import pandas as pd

def test_detect_doji_pattern():
    """Test Doji pattern detection"""
    # Arrange
    data = pd.DataFrame({
        'open': [100, 101, 102],
        'high': [102, 103, 104],
        'low': [99, 100, 101],
        'close': [100.1, 101.1, 102.1],  # Very close to open (Doji)
        'volume': [1000, 1100, 1200]
    })

    # Act
    patterns = detect_candlestick_patterns(data)

    # Assert
    assert 'doji' in patterns
    assert patterns['doji']['confidence'] > 0.8

def test_invalid_input_raises_error():
    """Test that invalid data raises appropriate error"""
    with pytest.raises(ValueError, match="Missing required columns"):
        detect_candlestick_patterns(pd.DataFrame({'invalid': [1, 2, 3]}))

def test_empty_dataframe_returns_no_patterns():
    """Test empty DataFrame handling"""
    empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    patterns = detect_candlestick_patterns(empty_df)
    assert len(patterns) == 0
```

### 3.2 Run Tests (Should Fail)
```bash
# Frontend
npm test -- PatternFilter.test.tsx

# Backend
pytest tests/test_pattern_detection.py -v
```

**Expected**: Tests fail because implementation doesn't exist yet. This confirms tests are valid.

### 3.3 Implement Feature

**Implementation Checklist**:
- [ ] TypeScript types defined
- [ ] Input validation added
- [ ] Error handling implemented
- [ ] Loading states managed
- [ ] Accessibility attributes added
- [ ] Security measures applied

**Example Implementation**:
```typescript
// PatternFilter.tsx
import React, { useState } from 'react';

interface PatternFilterProps {
  patterns: string[];
  onFilter: (selected: string[]) => void;
}

export const PatternFilter: React.FC<PatternFilterProps> = ({
  patterns,
  onFilter
}) => {
  const [selectedPatterns, setSelectedPatterns] = useState<string[]>([]);

  const handleToggle = (pattern: string) => {
    const updated = selectedPatterns.includes(pattern)
      ? selectedPatterns.filter(p => p !== pattern)
      : [...selectedPatterns, pattern];

    setSelectedPatterns(updated);
    onFilter(updated);
  };

  return (
    <div className="flex flex-wrap gap-2 p-4" role="group" aria-label="Pattern filter">
      {patterns.map(pattern => (
        <button
          key={pattern}
          onClick={() => handleToggle(pattern)}
          className={`
            px-4 py-2 rounded-lg font-medium transition-all
            ${selectedPatterns.includes(pattern)
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            }
          `}
          aria-pressed={selectedPatterns.includes(pattern)}
        >
          {pattern}
        </button>
      ))}
    </div>
  );
};
```

### 3.4 Run Tests (Should Pass)
```bash
npm test -- PatternFilter.test.tsx --coverage
```

**Expected**: All tests pass, coverage > 80%

---

## Phase 4: Validation (Frontend + Backend + Security)

### 4.1 Frontend Validation
```bash
cd /Users/tmkipper/Desktop/tk_projects/candlestick-screener

# Lint
npm run lint

# Type check
npx tsc --noEmit

# Build
npm run build

# Tests
npm test -- --coverage
```

**Success Criteria**:
- Zero lint errors
- Zero type errors
- Build successful
- All tests pass
- Coverage > 80%

### 4.2 Backend Validation
```bash
# Lint
flake8 *.py --max-line-length=120

# Type check
mypy *.py

# Tests
pytest --cov=. --cov-report=term-missing -v
```

**Success Criteria**:
- No style violations
- No type errors
- All tests pass
- Coverage > 85%

### 4.3 Security Validation
```bash
# Run security audit
python verify-deployment.py

# Check for secrets
git secrets --scan

# Dependency audit
npm audit --production
pip check
```

**Security Gates** (must pass all):
- [ ] No API keys in code
- [ ] Input validation on all user inputs
- [ ] Output sanitization on all displays
- [ ] Rate limiting configured
- [ ] HTTPS enforced
- [ ] Security headers set
- [ ] No critical vulnerabilities in dependencies

### 4.4 Integration Test
```bash
# Start dev server
npm run dev &

# Run integration tests
npm run test:integration

# Test Alpaca API integration
python quick_test.py
```

**Integration Checklist**:
- [ ] Frontend renders correctly
- [ ] API routes respond correctly
- [ ] Database queries work
- [ ] External APIs (Alpaca) functional
- [ ] Error handling works end-to-end

---

## Phase 5: Review (Security Audit)

### 5.1 Code Review Checklist

**Security Review**:
- [ ] No hardcoded secrets
- [ ] All inputs validated
- [ ] All outputs sanitized
- [ ] Error messages safe (no data leaks)
- [ ] Authentication/authorization correct
- [ ] Rate limiting applied

**Performance Review**:
- [ ] No unnecessary re-renders (React.memo)
- [ ] No unnecessary API calls (caching)
- [ ] No memory leaks (cleanup useEffect)
- [ ] Bundle size acceptable

**Code Quality Review**:
- [ ] DRY principle followed
- [ ] SOLID principles followed
- [ ] Meaningful variable names
- [ ] Comments on complex logic
- [ ] No console.log in production

### 5.2 Automated Security Scan
```bash
# OWASP dependency check
npm audit

# Snyk security scan (if configured)
snyk test

# Bandit for Python
bandit -r *.py
```

### 5.3 Manual Security Testing

**Test Cases**:
1. **SQL Injection**: Try `'; DROP TABLE users; --` in inputs
2. **XSS**: Try `<script>alert('XSS')</script>` in inputs
3. **CSRF**: Submit form without token
4. **Rate Limiting**: Make 100 requests in 1 second
5. **Authentication Bypass**: Access protected routes without login

---

## Phase 6: Documentation

### 6.1 Update TASK.md
```markdown
## Completed: <feature_name>

**Date**: 2025-11-30
**PRP**: PRPs/<feature>_prp.md

**Changes**:
- Created PatternFilter component
- Added pattern selection API endpoint
- Implemented Redis caching for patterns
- Updated security middleware

**Files Modified**:
- app/page.tsx
- app/components/PatternFilter.tsx
- api/patterns/route.ts
- lib/cache.ts

**Tests Added**:
- app/components/__tests__/PatternFilter.test.tsx (8 tests)
- tests/test_pattern_api.py (6 tests)

**Metrics**:
- Test Coverage: 87%
- Bundle Size: +15KB
- Security Rating: A+
- Performance: No degradation

**Next Steps**:
- Monitor production performance
- Gather user feedback
- Plan Phase 2 enhancements
```

### 6.2 Update PLANNING.md
Add new component to architecture diagram:
```markdown
## Component: PatternFilter

**Purpose**: Allow users to filter scan results by pattern type

**Location**: `app/components/PatternFilter.tsx`

**Props**:
- `patterns: string[]` - Available patterns
- `onFilter: (selected: string[]) => void` - Callback on selection

**State Management**: Local state (useState)

**Integration Points**:
- Parent: `app/page.tsx`
- API: `api/patterns/route.ts`
- Cache: Redis (5min TTL)
```

### 6.3 Update README (if user-facing)
```markdown
## New Feature: Pattern Filtering

You can now filter scan results by specific candlestick patterns:

1. Click "Filter Patterns" button
2. Select one or more patterns (Doji, Hammer, etc.)
3. Results update automatically

**Supported Patterns**: 60+ (see full list in docs)
```

---

## Completion Checklist

- [ ] Phase 1: Context loaded, prerequisites verified
- [ ] Phase 2: Tasks planned, security analyzed
- [ ] Phase 3: Tests written, implementation complete, tests pass
- [ ] Phase 4: Frontend validated, backend validated, security validated
- [ ] Phase 5: Code reviewed, security audited
- [ ] Phase 6: Documentation updated (TASK.md, PLANNING.md, README)
- [ ] Git commit created with descriptive message
- [ ] PR created (if multi-developer team)
- [ ] Deployed to staging for final testing

---

## Critical Rules Reminder

- **NO OpenAI** anywhere
- **TDD**: Tests before implementation
- **Security**: Validate inputs, sanitize outputs
- **API Keys**: .env only
- **Performance**: Monitor bundle size, response time
- **Documentation**: Update TASK.md and PLANNING.md

---

## Rollback Plan

If production issues occur:

1. **Immediate**: Revert deployment
   ```bash
   vercel rollback
   ```

2. **Investigate**: Check logs
   ```bash
   vercel logs --follow
   ```

3. **Fix**: Create hotfix branch
   ```bash
   git checkout -b hotfix/<issue>
   ```

4. **Test**: Run full validation
   ```bash
   /validate
   ```

5. **Deploy**: Push hotfix
   ```bash
   git push origin hotfix/<issue>
   vercel --prod
   ```
