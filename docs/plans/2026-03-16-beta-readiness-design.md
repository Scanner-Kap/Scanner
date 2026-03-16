# Beta Readiness Design

## Goal
Prepare the India First APK for beta distribution to friends: fix security gaps, add loading states so the UI never feels frozen, and clean up bad DB data.

## Scope (Option B)
1. Security audit — git history + APK bundle surface
2. Loading states — scanner and search screens
3. DB cleanup — remove "Maggie" stub record

## Section 1: Security Audit

### Two surfaces to check

**Surface 1: GitHub repo**
- Scan full git history for accidentally committed secrets (API keys, passwords, tokens)
- Verify `.gitignore` covers all `.env` files
- Fix anything found (rotate exposed keys, purge from history if needed)

**Surface 2: APK JS bundle**
- `EXPO_PUBLIC_*` variables are embedded in the JS bundle and extractable from any APK
- Currently only `EXPO_PUBLIC_BACKEND_URL` = Render URL → public API, safe to expose
- `ANTHROPIC_API_KEY` lives only in Render env vars → never in APK ✅
- `ADMIN_KEY` default is in `server.py` source → visible on GitHub but not in APK ✅
- Rule going forward: never put API keys in `EXPO_PUBLIC_*` variables

**What we produce:**
- Fix report: list of findings + actions taken
- `SECRETS.md`: one-page checklist of what lives where, so future contributors don't accidentally expose keys

### Known safe state (pre-audit baseline)
| Secret | Location | In APK? | In git? |
|--------|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Render env var | No | No |
| `POSTGRES_URL` | Render env var | No | No |
| `ADMIN_KEY` | `server.py` default string | No | Yes (low risk) |
| `EXPO_PUBLIC_BACKEND_URL` | `eas.json` + `.env` | Yes (safe — public URL) | `eas.json` yes, `.env` no |

## Section 2: Loading States

### Problem
App shows nothing while waiting for backend → feels frozen or broken to beta users.

### Fix per screen

**`scanner.tsx` — barcode scan:**
```
User scans barcode
→ Immediately show: spinner + "Looking up product..."
→ If >3 seconds: change message to "Almost there..."
→ On success: navigate to product-detail
→ On failure: show "Product not found" with a retry button
```

**`search.tsx` — brand search:**
- Already has an `ActivityIndicator` while loading
- Verify it shows correctly end-to-end with live backend
- No changes needed if working

**No skeleton screens** — spinners are sufficient for beta.

## Section 3: DB Cleanup

Delete the "Maggie" stub record (brand id=11) created by an OpenFoodFacts typo. This record has `ownership_country: Unknown` and would show a misleading score to beta users.

**Method:** Add a one-time `DELETE FROM brands WHERE brand_name = 'Maggie'` via a backend admin endpoint, or run directly via Render's PostgreSQL console.

## What's NOT in scope
- UptimeRobot keep-warm (user accepted cold start for first search)
- Brand intelligence plan (Claude generation, 1000 brands) — post-beta
- Play Store listing — post-beta

## Tech Stack
- Security scan: `git log`, `git grep`, `trufflehog` or manual grep
- Loading states: React Native `ActivityIndicator`, existing state management in `scanner.tsx`
- DB cleanup: Render PostgreSQL console (one SQL statement)
