# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**India First** — an FMCG product intelligence mobile app that scans barcodes, identifies products/brands, and calculates an "India Interest Score" (1-10 scale) based on ownership, manufacturing location, employment, and data sovereignty factors.

## Architecture

- **Frontend:** React Native / Expo 54 (TypeScript) — file-based routing via expo-router
- **Backend:** FastAPI (Python) — single-file server (`backend/server.py`) with all routes, models, DB schema, seed data, and scoring logic
- **Database:** PostgreSQL (psycopg2, no ORM)
- **Deployment:** Emergent Agent platform (preview at `makeininda.preview.emergentagent.com`)

### Frontend Structure (`frontend/app/`)
File-based routing with expo-router. Each file = a screen:
- `index.tsx` — Home screen
- `scanner.tsx` — Barcode scanner (expo-camera)
- `search.tsx` — Brand/product search
- `product-detail.tsx` / `brand-detail.tsx` — Detail views with score breakdowns

### Backend API Endpoints (all prefixed `/api`)
| Endpoint | Description |
|----------|-------------|
| `GET /` | Version info |
| `GET /product/barcode/{barcode}` | Lookup product by barcode |
| `GET /brand/{brand_id}` | Get brand details |
| `GET /search/brands?q=` | Search brands |
| `GET /search/products?q=` | Search products |
| `GET /score/{brand_id}` | Calculate India Interest Score |

### Scoring Algorithm (in `server.py`)
Weighted score calculation:
- Indian Company Ownership: 30%
- Manufacturing in India: 25%
- Country Relations: 20%
- Employment in India: 15%
- Data Sovereignty: 10%

## Common Commands

### Frontend
```bash
cd frontend
yarn install                        # Install dependencies
npx expo start                      # Start dev server (all platforms)
npx expo start --web --port 3000    # Start web only
npx expo lint                       # Run ESLint
npx expo run:android                # Run on Android
npx expo run:ios                    # Run on iOS
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Testing
```bash
python backend_test.py              # Run backend API tests (from root)
```

### Android APK Build
```bash
cd frontend
bash build-android.sh               # Requires Java 17+, Android SDK
```

## Environment Variables

| Variable | Used By | Default |
|----------|---------|---------|
| `POSTGRES_URL` | Backend | `postgresql://postgres:postgres@localhost:5432/india_first` |
| `EXPO_PUBLIC_BACKEND_URL` | Frontend | — |

## Key Technical Details

- **Node.js 20+ required** — Metro config uses `Array.toReversed()` which is unavailable in Node 18
- **Metro bundler** configured with max 2 workers and `.metro-cache/` disk cache
- **TypeScript path alias:** `@/*` maps to project root (`./`)
- Backend auto-creates tables and seeds 10 brands + 9 products on startup via `init_db()`
- CORS is fully open (all origins/methods/headers)
- Frontend uses `yarn` as package manager (yarn.lock present)
