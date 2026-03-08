# Brand Intelligence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix brand search (deploy backend to Railway), seed 1000 brands via JSON import, and add Claude API for on-the-fly brand creation and weekly data refresh.

**Architecture:** FastAPI backend deployed on Railway with PostgreSQL; frontend calls backend via public Railway URL set in EAS build env; Claude Haiku generates/refreshes brand data as structured JSON that maps directly to the existing scoring algorithm.

**Tech Stack:** FastAPI, psycopg2, `anthropic` Python SDK (backend); Expo/React Native, axios (frontend); Railway (hosting); `claude-haiku-4-5-20251001` (Claude model)

---

## Phase 1: Deploy Backend to Railway + Fix EAS Backend URL

### Task 1: Add `anthropic` to backend requirements

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add anthropic SDK**

Open `backend/requirements.txt` and add this line:
```
anthropic==0.49.0
```

Full file after edit:
```
fastapi==0.115.12
uvicorn==0.34.0
python-dotenv==1.0.1
psycopg2-binary==2.9.10
pydantic==2.10.5
starlette==0.41.3
anthropic==0.49.0
```

**Step 2: Verify it installs locally**
```bash
cd backend
pip install -r requirements.txt
python -c "import anthropic; print('OK')"
```
Expected: `OK`

**Step 3: Commit**
```bash
git add backend/requirements.txt
git commit -m "feat: add anthropic SDK to backend requirements"
```

---

### Task 2: Deploy backend to Railway

> Railway is a cloud hosting platform (railway.app). Free tier supports one small service + PostgreSQL. No credit card required for hobby plan.

**Step 1: Create Railway account**
- Go to https://railway.app and sign up with GitHub

**Step 2: Install Railway CLI**
```bash
npm install -g @railway/cli
railway login
```

**Step 3: Create new Railway project**
```bash
cd /Users/kapilsharma/Scanner/backend
railway init
```
When prompted: choose "Empty project", name it `india-first-backend`

**Step 4: Add PostgreSQL database**
In Railway dashboard (https://railway.app/dashboard):
- Click your project → "Add Service" → "Database" → "PostgreSQL"
- Wait ~30 seconds for it to provision
- Click the PostgreSQL service → "Connect" tab → copy the `DATABASE_URL` value (starts with `postgresql://`)

**Step 5: Set environment variables**
```bash
railway variables set POSTGRES_URL="<paste DATABASE_URL from step 4>"
railway variables set ANTHROPIC_API_KEY="<your Anthropic API key from console.anthropic.com>"
railway variables set ADMIN_KEY="india-first-admin-2024"
```

**Step 6: Create `backend/Procfile`** (tells Railway how to start the app)
```
web: uvicorn server:app --host 0.0.0.0 --port $PORT
```

**Step 7: Deploy**
```bash
cd /Users/kapilsharma/Scanner/backend
railway up
```
Wait for deploy to complete (~2 minutes). Railway will output a public URL like `https://india-first-backend-production.up.railway.app`

**Step 8: Verify deployment**
```bash
curl https://<your-railway-url>/api/
```
Expected: `{"message":"India First - FMCG Intelligence API","version":"1.0"}`

**Step 9: Test brand search works**
```bash
curl "https://<your-railway-url>/api/search/brands?q=amul"
```
Expected: JSON array with Amul brand data

**Step 10: Commit Procfile**
```bash
git add backend/Procfile
git commit -m "feat: add Procfile for Railway deployment"
```

---

### Task 3: Update EAS build with Railway URL

**Files:**
- Modify: `frontend/eas.json`

**Step 1: Update eas.json to include the backend URL**

Replace the entire contents of `frontend/eas.json` with:
```json
{
  "cli": {
    "version": ">= 16.0.0"
  },
  "build": {
    "preview": {
      "android": {
        "buildType": "apk"
      },
      "env": {
        "EXPO_PUBLIC_BACKEND_URL": "https://<your-railway-url>"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      },
      "env": {
        "EXPO_PUBLIC_BACKEND_URL": "https://<your-railway-url>"
      }
    }
  },
  "submit": {
    "production": {}
  }
}
```
Replace `<your-railway-url>` with the actual Railway URL from Task 2 Step 7.

**Step 2: Trigger a new EAS preview build**
```bash
cd /Users/kapilsharma/Scanner/frontend
npx eas-cli build --platform android --profile preview
```
Wait for build to complete. Install the new APK on device.

**Step 3: Verify brand search works on device**
- Open app → tap Search → type "Amul" → should return results

**Step 4: Commit**
```bash
git add frontend/eas.json
git commit -m "feat: add Railway backend URL to EAS build env"
```

---

## Phase 2: Brand Import Script (1000 brands via JSON chunks)

### Task 4: Add `POST /api/admin/import-brands` endpoint to backend

**Files:**
- Modify: `backend/server.py`

> The existing DB schema in `server.py` uses fields: `brand_name`, `parent_company`, `ownership_country`, `is_indian_company`, `manufactures_in_india`, `manufacturing_states`, `employees_in_india_estimate`, `data_storage_country`, `security_flags`, `govt_restrictions`, `source_links`.
>
> The JSON import format from the design doc maps to these fields. We'll accept a simplified format and translate.

**Step 1: Add Pydantic model for import**

In `backend/server.py`, after the existing model definitions (around line 280), add:
```python
class BrandImport(BaseModel):
    name: str
    country_of_origin: str
    indian_ownership_percent: float  # 0-100
    manufacturing_in_india: bool
    employment_in_india_percent: float  # 0-100
    data_sovereignty_score: int  # 1-10
    country_relations_score: int  # 1-10
    description: Optional[str] = None
    parent_company: Optional[str] = None

class BrandImportRequest(BaseModel):
    brands: List[BrandImport]
```

**Step 2: Add helper to convert import format to DB format**

Add this function to `backend/server.py` after the model definitions:
```python
def brand_import_to_db(b: BrandImport) -> dict:
    """Convert simplified import format to DB schema."""
    if b.manufacturing_in_india:
        manufactures = 'true'
    else:
        manufactures = 'false'

    # Convert percent to estimate string for employment
    if b.employment_in_india_percent >= 80:
        emp_estimate = '15000+'
    elif b.employment_in_india_percent >= 60:
        emp_estimate = '10000+'
    elif b.employment_in_india_percent >= 40:
        emp_estimate = '8000+'
    elif b.employment_in_india_percent >= 20:
        emp_estimate = '5000+'
    else:
        emp_estimate = '2000+'

    return {
        'brand_name': b.name,
        'parent_company': b.parent_company or b.name,
        'ownership_country': b.country_of_origin,
        'is_indian_company': b.country_of_origin.lower() == 'india',
        'manufactures_in_india': manufactures,
        'manufacturing_states': [],
        'employees_in_india_estimate': emp_estimate,
        'data_storage_country': b.country_of_origin,
        'security_flags': [],
        'govt_restrictions': [],
        'source_links': [],
    }
```

**Step 3: Add the import endpoint**

In `backend/server.py`, before the `app.include_router(api_router)` line, add:
```python
@api_router.post("/admin/import-brands")
async def import_brands(request: BrandImportRequest, x_admin_key: str = Header(None)):
    admin_key = os.environ.get('ADMIN_KEY', 'india-first-admin-2024')
    if x_admin_key != admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    imported = 0
    skipped = 0
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for b in request.brands:
            db_brand = brand_import_to_db(b)
            cursor.execute("""
                INSERT INTO brands (brand_name, parent_company, ownership_country, is_indian_company,
                    manufactures_in_india, manufacturing_states, employees_in_india_estimate,
                    data_storage_country, security_flags, govt_restrictions, source_links)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (brand_name) DO UPDATE SET
                    parent_company = EXCLUDED.parent_company,
                    ownership_country = EXCLUDED.ownership_country,
                    is_indian_company = EXCLUDED.is_indian_company,
                    manufactures_in_india = EXCLUDED.manufactures_in_india,
                    employees_in_india_estimate = EXCLUDED.employees_in_india_estimate,
                    data_storage_country = EXCLUDED.data_storage_country
            """, (
                db_brand['brand_name'], db_brand['parent_company'], db_brand['ownership_country'],
                db_brand['is_indian_company'], db_brand['manufactures_in_india'],
                db_brand['manufacturing_states'], db_brand['employees_in_india_estimate'],
                db_brand['data_storage_country'], db_brand['security_flags'],
                db_brand['govt_restrictions'], db_brand['source_links']
            ))
            if cursor.rowcount > 0:
                imported += 1
            else:
                skipped += 1
        conn.commit()

    return {"imported": imported, "skipped": skipped, "total": len(request.brands)}
```

Also add `Header` to the FastAPI imports at the top of `server.py`:
```python
from fastapi import FastAPI, APIRouter, HTTPException, Header
```

**Step 4: Test locally**
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

In a new terminal:
```bash
curl -X POST http://localhost:8001/api/admin/import-brands \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: india-first-admin-2024" \
  -d '{"brands": [{"name": "Haldirams", "country_of_origin": "India", "indian_ownership_percent": 100, "manufacturing_in_india": true, "employment_in_india_percent": 85, "data_sovereignty_score": 8, "country_relations_score": 9}]}'
```
Expected: `{"imported": 1, "skipped": 0, "total": 1}`

**Step 5: Commit and redeploy to Railway**
```bash
git add backend/server.py
git commit -m "feat: add /api/admin/import-brands endpoint"
cd backend && railway up
```

---

### Task 5: Create the brand import script

**Files:**
- Create: `scripts/import_brands.py`

**Step 1: Create `scripts/` directory and script**

Create `scripts/import_brands.py`:
```python
#!/usr/bin/env python3
"""
Import brands from a JSON file into the India First database.

Usage:
    python scripts/import_brands.py <json_file> [--url <backend_url>] [--key <admin_key>]

JSON format (array of brand objects):
[
  {
    "name": "Amul",
    "country_of_origin": "India",
    "indian_ownership_percent": 100,
    "manufacturing_in_india": true,
    "employment_in_india_percent": 95,
    "data_sovereignty_score": 8,
    "country_relations_score": 9,
    "description": "India's largest dairy cooperative",
    "parent_company": "GCMMF"
  }
]
"""
import sys
import json
import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description='Import brands from JSON file')
    parser.add_argument('json_file', help='Path to JSON file with brand data')
    parser.add_argument('--url', default='http://localhost:8001', help='Backend URL')
    parser.add_argument('--key', default='india-first-admin-2024', help='Admin key')
    args = parser.parse_args()

    with open(args.json_file, 'r', encoding='utf-8') as f:
        brands = json.load(f)

    if not isinstance(brands, list):
        print("ERROR: JSON file must contain an array of brand objects")
        sys.exit(1)

    print(f"Importing {len(brands)} brands to {args.url}...")

    response = requests.post(
        f"{args.url}/api/admin/import-brands",
        json={"brands": brands},
        headers={"X-Admin-Key": args.key},
        timeout=30,
    )

    if response.status_code != 200:
        print(f"ERROR: {response.status_code} - {response.text}")
        sys.exit(1)

    result = response.json()
    print(f"Done. Imported: {result['imported']}, Skipped (already exist): {result['skipped']}, Total: {result['total']}")

if __name__ == '__main__':
    main()
```

**Step 2: Install requests if not already present**
```bash
pip install requests
```

**Step 3: Create a sample test JSON to verify the script works**

Create `scripts/sample_brands.json`:
```json
[
  {
    "name": "Haldirams",
    "country_of_origin": "India",
    "indian_ownership_percent": 100,
    "manufacturing_in_india": true,
    "employment_in_india_percent": 85,
    "data_sovereignty_score": 8,
    "country_relations_score": 9,
    "description": "Leading Indian snacks brand",
    "parent_company": "Haldiram Foods International"
  },
  {
    "name": "ITC",
    "country_of_origin": "India",
    "indian_ownership_percent": 100,
    "manufacturing_in_india": true,
    "employment_in_india_percent": 90,
    "data_sovereignty_score": 9,
    "country_relations_score": 9,
    "description": "Diversified Indian conglomerate",
    "parent_company": "ITC Limited"
  }
]
```

**Step 4: Run the script against local server**
```bash
# Make sure local server is running first
python scripts/import_brands.py scripts/sample_brands.json --url http://localhost:8001
```
Expected: `Done. Imported: 2, Skipped (already exist): 0, Total: 2`

**Step 5: Run again to verify idempotency**
```bash
python scripts/import_brands.py scripts/sample_brands.json --url http://localhost:8001
```
Expected: `Done. Imported: 2, Skipped (already exist): 0, Total: 2`
(Upsert updates existing records, so `imported` count reflects upserted rows)

**Step 6: Test against Railway**
```bash
python scripts/import_brands.py scripts/sample_brands.json \
  --url https://<your-railway-url> \
  --key india-first-admin-2024
```
Expected: same success output

**Step 7: Commit**
```bash
git add scripts/import_brands.py scripts/sample_brands.json
git commit -m "feat: add brand import script for JSON chunks"
```

> **To import your 1000 brands:** Split your data into JSON files of ≤50 brands each and run:
> ```bash
> python scripts/import_brands.py brands_chunk_01.json --url https://<railway-url> --key india-first-admin-2024
> python scripts/import_brands.py brands_chunk_02.json --url https://<railway-url> --key india-first-admin-2024
> # ... repeat for each chunk
> ```

---

## Phase 3: Claude API — On-the-Fly Brand Generation

### Task 6: Add `POST /api/brand/generate` endpoint

**Files:**
- Modify: `backend/server.py`

**Step 1: Add import for anthropic at top of `server.py`**

After the existing imports, add:
```python
import anthropic
```

**Step 2: Add Claude client initialization**

After the `POSTGRES_URL` line (around line 17), add:
```python
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ADMIN_KEY = os.environ.get('ADMIN_KEY', 'india-first-admin-2024')
```

**Step 3: Add brand generation helper function**

Add this function to `server.py` after the `brand_import_to_db` function:
```python
def generate_brand_with_claude(brand_name: str) -> dict:
    """Call Claude API to generate brand data. Returns dict in BrandImport format."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are a brand intelligence analyst for India First, an app that rates how much a brand benefits India.

Analyze the brand: "{brand_name}"

Return ONLY valid JSON (no markdown, no explanation) with exactly these fields:
{{
  "name": "{brand_name}",
  "country_of_origin": "country where brand/parent company is headquartered",
  "indian_ownership_percent": <0-100, percentage of company owned by Indian entities>,
  "manufacturing_in_india": <true if primarily manufactured in India, false otherwise>,
  "employment_in_india_percent": <0-100, estimated percentage of workforce based in India>,
  "data_sovereignty_score": <1-10, 10=data stored in India, 1=data stored abroad>,
  "country_relations_score": <1-10, 10=India or close ally, 1=adversarial nation>,
  "description": "one sentence description of the brand",
  "parent_company": "name of parent company"
}}

Use your knowledge of publicly known information. If uncertain, use conservative estimates. Never fabricate specific numbers you don't know."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    return json.loads(raw)
```

Also add `import json` to the imports at top of `server.py` (if not already present).

**Step 4: Add Pydantic model for generate request**

After the existing model definitions, add:
```python
class BrandGenerateRequest(BaseModel):
    name: str
```
```python
class BrandGenerateResponse(BaseModel):
    id: int
    brand_name: str
    score: float
    recommendation: str
    breakdown: dict
    generated: bool  # True if newly created, False if already existed
```

**Step 5: Add the generate endpoint**

Add before `app.include_router(api_router)`:
```python
@api_router.post("/brand/generate", response_model=BrandGenerateResponse)
async def generate_brand(request: BrandGenerateRequest):
    brand_name = request.name.strip()
    if not brand_name:
        raise HTTPException(status_code=400, detail="Brand name required")

    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if brand already exists
        cursor.execute(
            "SELECT * FROM brands WHERE LOWER(brand_name) = LOWER(%s)",
            (brand_name,)
        )
        existing = cursor.fetchone()
        if existing:
            brand = dict(existing)
            score_data = calculate_india_score(brand)
            return {**score_data, "id": brand["id"], "brand_name": brand["brand_name"], "generated": False}

        # Generate with Claude
        if not ANTHROPIC_API_KEY:
            raise HTTPException(status_code=503, detail="Brand generation unavailable")

        try:
            brand_data = generate_brand_with_claude(brand_name)
        except Exception as e:
            logger.error(f"Claude generation failed for {brand_name}: {e}")
            raise HTTPException(status_code=503, detail="Could not generate brand data. Try again later.")

        # Convert to DB format and insert
        db_brand = brand_import_to_db(BrandImport(**brand_data))
        cursor.execute("""
            INSERT INTO brands (brand_name, parent_company, ownership_country, is_indian_company,
                manufactures_in_india, manufacturing_states, employees_in_india_estimate,
                data_storage_country, security_flags, govt_restrictions, source_links)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (brand_name) DO UPDATE SET brand_name = EXCLUDED.brand_name
            RETURNING id
        """, (
            db_brand['brand_name'], db_brand['parent_company'], db_brand['ownership_country'],
            db_brand['is_indian_company'], db_brand['manufactures_in_india'],
            db_brand['manufacturing_states'], db_brand['employees_in_india_estimate'],
            db_brand['data_storage_country'], db_brand['security_flags'],
            db_brand['govt_restrictions'], db_brand['source_links']
        ))
        new_id = cursor.fetchone()['id']
        conn.commit()

        # Fetch inserted brand for scoring
        cursor.execute("SELECT * FROM brands WHERE id = %s", (new_id,))
        brand = dict(cursor.fetchone())
        score_data = calculate_india_score(brand)
        return {**score_data, "id": brand["id"], "brand_name": brand["brand_name"], "generated": True}
```

**Step 6: Test locally**
```bash
# Start server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# In another terminal (need ANTHROPIC_API_KEY in your env)
export ANTHROPIC_API_KEY="sk-ant-..."
curl -X POST http://localhost:8001/api/brand/generate \
  -H "Content-Type: application/json" \
  -d '{"name": "Tata Salt"}'
```
Expected: JSON with `score`, `recommendation`, `breakdown`, `generated: true`

**Step 7: Run again for same brand (should return existing)**
```bash
curl -X POST http://localhost:8001/api/brand/generate \
  -H "Content-Type: application/json" \
  -d '{"name": "Tata Salt"}'
```
Expected: Same response but `generated: false`

**Step 8: Commit and redeploy**
```bash
git add backend/server.py
git commit -m "feat: add /api/brand/generate endpoint with Claude API"
cd backend && railway up
```

---

### Task 7: Update frontend search to trigger on-the-fly generation

**Files:**
- Modify: `frontend/app/search.tsx`

> Current behavior (lines 212-219 in search.tsx): when `results.length === 0` and `searchQuery` is set, shows "No results found" static message.
> New behavior: when brand search returns 0 results, call `/api/brand/generate` and show the result.

**Step 1: Add `generating` state variable**

In `frontend/app/search.tsx`, in the `SearchScreen` function after the existing state declarations (around line 35), add:
```typescript
const [generating, setGenerating] = useState(false);
const [generateError, setGenerateError] = useState<string | null>(null);
```

**Step 2: Add generate function**

After the `handleSearch` function (around line 56), add:
```typescript
const handleGenerate = async (brandName: string) => {
  setGenerating(true);
  setGenerateError(null);
  try {
    const response = await axios.post(
      `${EXPO_PUBLIC_BACKEND_URL}/api/brand/generate`,
      { name: brandName },
      { timeout: 20000 }
    );
    const generated = response.data;
    // Navigate directly to brand detail
    router.push({
      pathname: '/brand-detail',
      params: { brandId: generated.id.toString() },
    });
  } catch (error) {
    setGenerateError('Could not generate brand data. Please try again.');
  } finally {
    setGenerating(false);
  }
};
```

**Step 3: Update the empty state UI**

Replace the existing "No results found" block in the JSX (lines 212-220 in search.tsx):
```tsx
) : searchQuery && !loading ? (
  <View style={styles.emptyState}>
    <Ionicons name="search-outline" size={64} color="#666" />
    <Text style={styles.emptyText}>No results found</Text>
    <Text style={styles.emptySubtext}>
      Try searching for popular brands like Amul, Parle, or Nestle
    </Text>
  </View>
```

Replace with:
```tsx
) : searchQuery && !loading ? (
  <View style={styles.emptyState}>
    {generating ? (
      <>
        <ActivityIndicator size="large" color="#FF9933" />
        <Text style={styles.emptyText}>Generating brand data...</Text>
        <Text style={styles.emptySubtext}>Asking AI about "{searchQuery}"</Text>
      </>
    ) : generateError ? (
      <>
        <Ionicons name="alert-circle-outline" size={64} color="#FF9933" />
        <Text style={styles.emptyText}>Brand not found</Text>
        <Text style={styles.emptySubtext}>{generateError}</Text>
      </>
    ) : (
      <>
        <Ionicons name="search-outline" size={64} color="#666" />
        <Text style={styles.emptyText}>Not in our database</Text>
        <Text style={styles.emptySubtext}>Tap below to look up "{searchQuery}" using AI</Text>
        <TouchableOpacity
          style={[styles.searchButton, { marginTop: 16, marginHorizontal: 0 }]}
          onPress={() => handleGenerate(searchQuery)}
        >
          <Text style={styles.searchButtonText}>Generate Brand Data</Text>
        </TouchableOpacity>
      </>
    )}
  </View>
```

**Step 4: Reset generate state on new search**

In `handleSearch` function, add at the beginning (after the null check):
```typescript
setGenerateError(null);
setGenerating(false);
```

Also reset when switching tabs — in the `setSearchType` calls, add:
```typescript
setGenerateError(null);
setGenerating(false);
```

**Step 5: Build and test**
```bash
cd frontend
npx eas-cli build --platform android --profile preview
```
Install APK → Search for "Tata Namak" (not in DB) → should show "Generate Brand Data" button → tap → navigates to brand detail with AI-generated score.

**Step 6: Commit**
```bash
git add frontend/app/search.tsx
git commit -m "feat: add AI brand generation from search empty state"
```

---

## Phase 4: Weekly Refresh Engine

### Task 8: Add `POST /api/admin/refresh-brands` endpoint

**Files:**
- Modify: `backend/server.py`

**Step 1: Add the refresh endpoint**

Add before `app.include_router(api_router)`:
```python
@api_router.post("/admin/refresh-brands")
async def refresh_brands(x_admin_key: str = Header(None)):
    admin_key = os.environ.get('ADMIN_KEY', 'india-first-admin-2024')
    if x_admin_key != admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, brand_name FROM brands ORDER BY id")
        all_brands = cursor.fetchall()

    updated = 0
    failed = 0
    batch_size = 10

    for i in range(0, len(all_brands), batch_size):
        batch = all_brands[i:i + batch_size]
        for brand_row in batch:
            try:
                brand_data = generate_brand_with_claude(brand_row['brand_name'])
                db_brand = brand_import_to_db(BrandImport(**brand_data))
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE brands SET
                            parent_company = %s,
                            ownership_country = %s,
                            is_indian_company = %s,
                            manufactures_in_india = %s,
                            employees_in_india_estimate = %s,
                            data_storage_country = %s
                        WHERE id = %s
                    """, (
                        db_brand['parent_company'], db_brand['ownership_country'],
                        db_brand['is_indian_company'], db_brand['manufactures_in_india'],
                        db_brand['employees_in_india_estimate'], db_brand['data_storage_country'],
                        brand_row['id']
                    ))
                    conn.commit()
                updated += 1
                logger.info(f"Refreshed: {brand_row['brand_name']}")
            except Exception as e:
                failed += 1
                logger.error(f"Failed to refresh {brand_row['brand_name']}: {e}")

    return {"updated": updated, "failed": failed, "total": len(all_brands)}
```

**Step 2: Test locally (only refresh a few brands to save API calls)**
```bash
# With local server running and ANTHROPIC_API_KEY set:
curl -X POST http://localhost:8001/api/admin/refresh-brands \
  -H "X-Admin-Key: india-first-admin-2024"
```
Expected: `{"updated": 10, "failed": 0, "total": 10}` (10 seeded brands)

**Step 3: Commit and redeploy**
```bash
git add backend/server.py
git commit -m "feat: add /api/admin/refresh-brands endpoint"
cd backend && railway up
```

---

### Task 9: Create the weekly refresh script

**Files:**
- Create: `scripts/refresh_brands.py`

**Step 1: Create `scripts/refresh_brands.py`**
```python
#!/usr/bin/env python3
"""
Weekly brand refresh script — calls Claude API to update all brand data.

Usage:
    python scripts/refresh_brands.py [--url <backend_url>] [--key <admin_key>]

Typical runtime: ~15-20 minutes for 1000 brands (Claude rate limits).
Run this manually once a week.
"""
import argparse
import requests
import sys
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Refresh all brand data using Claude API')
    parser.add_argument('--url', default='http://localhost:8001', help='Backend URL')
    parser.add_argument('--key', default='india-first-admin-2024', help='Admin key')
    args = parser.parse_args()

    print(f"[{datetime.now().isoformat()}] Starting weekly brand refresh...")
    print(f"Backend: {args.url}")
    print("This may take 15-20 minutes for large brand lists. Do not interrupt.")

    response = requests.post(
        f"{args.url}/api/admin/refresh-brands",
        headers={"X-Admin-Key": args.key},
        timeout=1800,  # 30 minute timeout
    )

    if response.status_code != 200:
        print(f"ERROR: {response.status_code} - {response.text}")
        sys.exit(1)

    result = response.json()
    print(f"\n[{datetime.now().isoformat()}] Refresh complete.")
    print(f"  Updated: {result['updated']}")
    print(f"  Failed:  {result['failed']}")
    print(f"  Total:   {result['total']}")

    if result['failed'] > 0:
        print(f"\nWARNING: {result['failed']} brands failed to refresh. Check server logs.")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**Step 2: Test against Railway**
```bash
python scripts/refresh_brands.py \
  --url https://<your-railway-url> \
  --key india-first-admin-2024
```
Expected: progress logs + final summary. Runtime ~1 second per brand.

**Step 3: Commit**
```bash
git add scripts/refresh_brands.py
git commit -m "feat: add weekly brand refresh script"
```

---

## Final Verification

After all tasks complete, verify the full flow:

1. **Search works:** Open app → Search "Amul" → results appear
2. **On-the-fly generation:** Search "Tata Namak" (not in DB) → "Generate Brand Data" button → tap → brand detail appears with score
3. **Import script:** `python scripts/import_brands.py scripts/sample_brands.json --url https://<railway-url>` → success
4. **Refresh script:** `python scripts/refresh_brands.py --url https://<railway-url>` → all brands updated

```bash
git push origin claude/build-scanner-app-axlSK
```
