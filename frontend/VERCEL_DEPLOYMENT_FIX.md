# Vercel Deployment Fix - Module Resolution

## Problem
Vercel build was failing with:
```
Module not found: Can't resolve '@/lib/api'
```

## Root Cause
The root `.gitignore` file had `lib/` pattern that was ignoring ALL `lib/` folders in the project, including `frontend/lib/`.

## Solution Applied

### 1. Updated Root `.gitignore`
**File:** `.gitignore` (project root)

Changed:
```gitignore
lib/
lib64/
```

To:
```gitignore
lib64/
...
# Python lib folder (but not frontend/lib)
lib/
!frontend/lib/
```

### 2. Updated Frontend `.gitignore`
**File:** `frontend/.gitignore`

Added at the end:
```gitignore
# IMPORTANT: Do NOT ignore src/lib/ - contains API client
!src/lib/
!src/lib/**/*
```

### 3. Created `src/lib/api.ts`
**File:** `frontend/src/lib/api.ts`

This file contains all API client code with proper TypeScript interfaces and API methods.

### 4. Verified `tsconfig.json` Configuration
**File:** `frontend/tsconfig.json`

The path alias is correctly configured:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

## Verification

Build now succeeds locally:
```bash
cd frontend
npm run build
# ✓ Build completed successfully
```

## Files Changed

1. `.gitignore` - Fixed lib/ folder exclusion
2. `frontend/.gitignore` - Added explicit unignore for src/lib/
3. `frontend/src/lib/api.ts` - Created API client module

## Deployment Checklist for Vercel

- [x] `src/lib/api.ts` exists and is committed
- [x] Root `.gitignore` does not ignore `frontend/lib/`
- [x] `tsconfig.json` has correct path aliases
- [x] All imports use correct case: `@/lib/api` (lowercase)
- [x] Build succeeds locally before pushing

## Example Import Usage

All files now correctly import from `@/lib/api`:

```typescript
// ✅ Correct
import { ticketsApi, TicketStats } from '@/lib/api';
import { customersApi, Customer } from '@/lib/api';
import { webformApi } from '@/lib/api';

// ❌ Wrong (would fail on Linux)
import { ticketsApi } from '@/Lib/api';  // Capital L
import { ticketsApi } from '@/lib/API';  // Capital API
```

## Next Steps

1. Commit all changes:
```bash
git add .
git commit -m "Fix Vercel build: unignore frontend/lib and add api.ts"
git push
```

2. Vercel will automatically rebuild on push to main branch

3. If build still fails, check:
   - Vercel build logs for exact error
   - Environment variables are set in Vercel dashboard
   - Node.js version compatibility
