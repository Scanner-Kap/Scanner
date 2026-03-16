# Beta Readiness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prepare the India First APK for beta distribution: security audit, improved loading UX in the scanner, and DB cleanup.

**Architecture:** Three independent tasks — security scan (read-only audit + SECRETS.md), scanner UX improvement (add timeout-based message + full-screen overlay), and DB cleanup (one SQL statement via Render console). No backend changes. Frontend change is scanner.tsx only.

**Tech Stack:** git (audit), React Native ActivityIndicator (loading overlay), Render PostgreSQL console (DB cleanup)

---

## Task 1: Security Audit

**Files:**
- Create: `SECRETS.md` (repo root)

> This task is read-only except for creating SECRETS.md. Run all commands from `/Users/kapilsharma/Scanner`.

**Step 1: Scan git history for secrets patterns**

```bash
cd /Users/kapilsharma/Scanner
git log --all --full-history --oneline | head -30
```

Then scan all commits for secret-like patterns:
```bash
git grep -i "sk-ant\|api_key\|apikey\|secret\|password\|token\|private_key" \
  $(git log --all --format="%H") -- "*.py" "*.ts" "*.tsx" "*.js" "*.json" "*.env*" 2>/dev/null | head -50
```

**Step 2: Scan current tracked files**

```bash
grep -r "sk-ant\|ANTHROPIC_API_KEY\s*=\s*['\"][^$]" \
  --include="*.py" --include="*.ts" --include="*.tsx" \
  --include="*.js" --include="*.json" \
  /Users/kapilsharma/Scanner/
```

Also check for any .env files accidentally tracked:
```bash
git ls-files | grep -i "\.env"
```
Expected: empty output (no .env files tracked)

**Step 3: Verify .gitignore coverage**

```bash
cat /Users/kapilsharma/Scanner/frontend/.gitignore | grep -i env
cat /Users/kapilsharma/Scanner/.gitignore | grep -i env
```
Expected: `.env` entries present in both

**Step 4: Check eas.json for sensitive values**

```bash
cat /Users/kapilsharma/Scanner/frontend/eas.json
```
Expected: only `EXPO_PUBLIC_BACKEND_URL` = public Render URL. No API keys.

**Step 5: Create `SECRETS.md` at repo root**

Create `/Users/kapilsharma/Scanner/SECRETS.md`:
```markdown
# Secrets & Credentials Reference

This document tracks where each secret lives so nothing is accidentally
committed or bundled into the APK.

## Rule: Never put API keys in EXPO_PUBLIC_* variables
EXPO_PUBLIC_* variables are embedded in the JS bundle and can be extracted
from any APK by anyone who downloads it.

## Secrets Map

| Secret | Where it lives | In APK? | In git? | Notes |
|--------|---------------|---------|---------|-------|
| `ANTHROPIC_API_KEY` | Render env vars only | No | No | Never commit |
| `POSTGRES_URL` | Render env vars only | No | No | Never commit |
| `ADMIN_KEY` | Render env vars + server.py default | No | Yes (default only) | Default is low-risk; override in prod |
| `EXPO_PUBLIC_BACKEND_URL` | eas.json + frontend/.env | Yes (safe) | eas.json yes | Public URL, safe to expose |

## Safe to commit
- `eas.json` (contains only the public backend URL)
- `backend/server.py` (reads secrets from env vars, never hardcodes real values)

## Never commit
- `frontend/.env` (gitignored ✅)
- `backend/.env` (gitignored ✅)
- Any file containing real API keys, passwords, or tokens

## Rotating a compromised key
1. Immediately generate a new key at the provider (Anthropic Console, etc.)
2. Update the Render environment variable
3. The old key is now invalid — no code changes needed
```

**Step 6: Commit**

```bash
cd /Users/kapilsharma/Scanner
git add SECRETS.md
git commit -m "docs: add SECRETS.md with credentials reference and APK safety guide"
git push origin claude/build-scanner-app-axlSK
```

**Step 7: Report findings**

After running the scans, report:
- Any secrets found in git history → list them
- Any .env files tracked in git → list them
- Any EXPO_PUBLIC_* variables containing non-public values → list them
- Overall verdict: ✅ Clean or ❌ Issues found (and what was done)

---

## Task 2: Scanner Loading State Improvement

**Files:**
- Modify: `frontend/app/scanner.tsx`

> **Context:** `scanner.tsx` already has a `loading` state and shows "Fetching product information..." + a small `ActivityIndicator` at the bottom during loading (lines 146-150). The current UX problem: the camera view stays visible while loading, so the user isn't sure if anything is happening. We'll add a full-screen overlay during loading + a timeout-based message change after 3 seconds.

**Step 1: Add `loadingMessage` state**

In `scanner.tsx`, find the existing state declarations (around line 20-22):
```typescript
const [hasPermission, setHasPermission] = useState<boolean | null>(null);
const [scanned, setScanned] = useState(false);
const [loading, setLoading] = useState(false);
```

Add one more state:
```typescript
const [loadingMessage, setLoadingMessage] = useState('Looking up product...');
```

**Step 2: Add timeout message in `handleBarcodeScanned`**

Find `handleBarcodeScanned` (line 31). After `setLoading(true)`, add:
```typescript
setLoadingMessage('Looking up product...');
const slowTimer = setTimeout(() => {
  setLoadingMessage('Almost there...');
}, 3000);
```

Then in the `finally` block, clear the timer:
```typescript
} finally {
  clearTimeout(slowTimer);
  setLoading(false);
}
```

> Note: `slowTimer` must be declared before the try block so it's accessible in finally. Declare it as:
> ```typescript
> let slowTimer: ReturnType<typeof setTimeout>;
> ```
> before the `try` statement, then assign inside `try`.

**Step 3: Add full-screen loading overlay to JSX**

Find the main return statement (line 111). Inside `<SafeAreaView style={styles.container}>`, add a loading overlay right after the opening tag, before `<View style={styles.header}>`:

```tsx
{loading && (
  <View style={styles.loadingOverlay}>
    <ActivityIndicator size="large" color="#FF9933" />
    <Text style={styles.loadingOverlayText}>{loadingMessage}</Text>
  </View>
)}
```

**Step 4: Add overlay styles**

In the `StyleSheet.create({...})` block at the bottom, add:
```typescript
loadingOverlay: {
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(26, 26, 46, 0.92)',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 10,
},
loadingOverlayText: {
  color: '#fff',
  fontSize: 18,
  marginTop: 16,
  fontWeight: '600',
},
```

**Step 5: Remove the old inline loading indicator**

The existing small loading text + indicator at the bottom (lines 146-150) is now redundant since we have the full-screen overlay. Remove these lines from the `<View style={styles.instructions}>` block:
```tsx
{loading
  ? 'Fetching product information...'
  : 'Align the barcode within the frame'}
```
Replace with just:
```tsx
{'Align the barcode within the frame'}
```

And remove:
```tsx
{loading && <ActivityIndicator size="small" color="#FF9933" style={{ marginTop: 8 }} />}
```

**Step 6: Verify the final `handleBarcodeScanned` function looks like this:**

```typescript
const handleBarcodeScanned = async ({ data }: { data: string }) => {
  if (scanned || loading) return;

  setScanned(true);
  setLoading(true);
  setLoadingMessage('Looking up product...');

  let slowTimer: ReturnType<typeof setTimeout>;
  try {
    slowTimer = setTimeout(() => {
      setLoadingMessage('Almost there...');
    }, 3000);

    const response = await axios.get(
      `${EXPO_PUBLIC_BACKEND_URL}/api/product/barcode/${data}`
    );

    router.push({
      pathname: '/product-detail',
      params: { productData: JSON.stringify(response.data) },
    });
  } catch (error: any) {
    if (error.response?.status === 404) {
      Alert.alert(
        'Product Not Found',
        `Barcode: ${data}\n\nThis product is not in our database yet.`,
        [
          {
            text: 'Scan Again',
            onPress: () => {
              setScanned(false);
              setLoading(false);
            },
          },
          {
            text: 'Go Back',
            onPress: () => router.back(),
          },
        ]
      );
    } else {
      Alert.alert(
        'Error',
        'Failed to fetch product information. Please try again.',
        [
          {
            text: 'Try Again',
            onPress: () => {
              setScanned(false);
              setLoading(false);
            },
          },
        ]
      );
    }
  } finally {
    clearTimeout(slowTimer!);
    setLoading(false);
  }
};
```

**Step 7: Commit and push**

```bash
cd /Users/kapilsharma/Scanner
git add frontend/app/scanner.tsx
git commit -m "feat: add full-screen loading overlay with timeout message to scanner"
git push origin claude/build-scanner-app-axlSK
```

---

## Task 3: DB Cleanup (Manual — requires Render console)

> This task is manual. No code changes. You (the user) run one SQL statement in the Render PostgreSQL console.

**Step 1: Open Render PostgreSQL console**
- Go to https://render.com/dashboard
- Click your PostgreSQL database service
- Click the **"Connect"** tab → **"PSQL Command"** → copy the command
- Run it in your terminal to open a psql session

OR use the **"Query"** tab in the Render dashboard if available.

**Step 2: Verify the stub record exists**
```sql
SELECT id, brand_name, ownership_country FROM brands WHERE brand_name = 'Maggie';
```
Expected: 1 row with `ownership_country = 'Unknown'`

**Step 3: Delete it**
```sql
DELETE FROM brands WHERE brand_name = 'Maggie' AND ownership_country = 'Unknown';
```
Expected: `DELETE 1`

**Step 4: Verify it's gone**
```sql
SELECT id, brand_name FROM brands WHERE brand_name ILIKE '%maggi%';
```
Expected: only `Maggi` (id=7) with `ownership_country = 'Switzerland'` — no `Maggie` stub.

---

## Final Step: Build Beta APK

After all three tasks are complete:

```bash
cd /Users/kapilsharma/Scanner/frontend
npx eas-cli build --platform android --profile preview
```

Share the resulting APK link with beta testers.
