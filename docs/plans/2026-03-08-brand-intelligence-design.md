# Brand Intelligence Design

## Goal
Fix brand search, seed 1000 brands via JSON import, and add Claude API for on-the-fly brand creation and weekly data refresh.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Expo)                    │
│  Search "Amul" → found → show result                 │
│  Search "XYZ" → not found → call /brand/generate     │
│                → Claude creates entry → show result  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Backend (FastAPI on Railway)             │
│                                                      │
│  GET  /api/search/brands?q=       (existing)         │
│  GET  /api/score/{brand_id}       (existing)         │
│  POST /api/brand/generate         (NEW) ← frontend   │
│  POST /api/admin/refresh-brands   (NEW) ← script     │
│  POST /api/admin/import-brands    (NEW) ← seed script│
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼──────┐             ┌────────▼───────┐
│  PostgreSQL  │             │  Claude API    │
│  (Railway)   │             │  (Anthropic)   │
│  1000 brands │             │  Structured    │
│  seed data   │             │  brand data    │
└──────────────┘             └────────────────┘
```

## Components

### 1. Brand seed import script (`scripts/import_brands.py`)
- Accepts a JSON file of up to 50 brands at a time
- Upserts into DB (safe to run multiple times)
- Run 20 times to load all 1000 brands
- JSON schema per brand:
  ```json
  {
    "name": "Amul",
    "country_of_origin": "India",
    "indian_ownership_percent": 100,
    "manufacturing_in_india": true,
    "employment_in_india_percent": 95,
    "data_sovereignty_score": 8,
    "country_relations_score": 9,
    "description": "India's largest dairy cooperative"
  }
  ```

### 2. Railway deployment
- Deploy `backend/server.py` to Railway (free tier)
- Set `ANTHROPIC_API_KEY` and `POSTGRES_URL` as Railway env vars
- Update `eas.json` with Railway public URL as `EXPO_PUBLIC_BACKEND_URL`
- Rebuild EAS preview APK

### 3. `POST /api/brand/generate` (new backend endpoint)
- Input: `{"name": "brand name"}`
- Checks DB first — returns existing if found
- Calls Claude API with structured prompt
- Stores result in DB
- Returns brand + score
- Error: Claude failure → HTTP 503 with message (no crash)

### 4. `POST /api/admin/refresh-brands` (new backend endpoint)
- Fetches all brand names from DB
- Calls Claude for each in batches of 10
- Updates brand records with fresh data
- Protected by a simple secret header (`X-Admin-Key`)

### 5. `scripts/refresh_brands.py` (weekly manual script)
- Hits `/api/admin/refresh-brands` with admin key
- Run manually for now; can be cronjobed later
- Logs progress per brand

### 6. Frontend search change (`frontend/app/search.tsx`)
- Current: no results → "Nothing found"
- New: no results → show "Generating brand data..." spinner → `POST /api/brand/generate` → display result
- On Claude failure: show "Brand not found. Try again later."

## Data Flow

### On-the-fly brand creation:
```
User searches "Patanjali" → 0 DB results
→ Frontend shows loading spinner
→ POST /api/brand/generate {"name": "Patanjali"}
→ Backend checks DB (double-check, could have been created concurrently)
→ Calls Claude: structured JSON prompt → parses response
→ INSERT into brands table
→ GET /api/score/{brand_id} → return brand + score
→ Frontend displays result
Total: ~3-5 seconds
```

### Weekly refresh:
```
Developer runs: python scripts/refresh_brands.py
→ GET all brand names from DB
→ For each batch of 10:
    → Call Claude with brand name → get updated JSON
    → UPDATE brands table
→ Scores auto-reflect on next frontend request
~1000 brands ≈ 15-20 min runtime
```

### Initial seed:
```
Developer runs: python scripts/import_brands.py brands_chunk_1.json
→ Reads JSON array of ≤50 brands
→ UPSERT each into DB (skips duplicates)
→ Repeat 20 times for 1000 brands
```

## Error Handling
- Claude API down → `POST /api/brand/generate` returns 503, frontend shows "try again"
- Generation timeout (>15s) → same 503 fallback
- Duplicate brand name → upsert (update existing, don't create duplicate)
- Import script: invalid JSON → clear error message, no partial writes

## Tech Stack
- Backend: FastAPI, psycopg2, `anthropic` Python SDK
- Frontend: Expo / React Native, axios
- Database: PostgreSQL on Railway
- Claude model: `claude-haiku-4-5-20251001` for brand generation (fast + cheap)
- Hosting: Railway (backend + DB)

## Phases
1. **Deploy backend to Railway** + fix `EXPO_PUBLIC_BACKEND_URL` in EAS → search works
2. **Add import script** + user provides JSON chunks → 1000 brands seeded
3. **Add `/api/brand/generate`** + frontend loading state → on-the-fly creation works
4. **Add `/api/admin/refresh-brands`** + weekly script → live engine works
