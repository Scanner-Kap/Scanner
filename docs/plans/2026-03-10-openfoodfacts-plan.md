# OpenFoodFacts Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update `/api/product/barcode/{barcode}` to fall back to OpenFoodFacts when a barcode isn't in the DB, then look up or generate the brand's India Interest Score via Claude.

**Architecture:** Backend-only change. When barcode not in DB, call OpenFoodFacts API to get product name + brand name, look up brand in DB (or generate via Claude if missing), cache product in DB, return combined product + score response. Frontend unchanged.

**Tech Stack:** FastAPI, httpx (async HTTP), psycopg2, anthropic SDK, OpenFoodFacts public API

---

## Task 1: Add `httpx` to backend requirements

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add httpx**

Open `backend/requirements.txt` and add:
```
httpx==0.28.1
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
httpx==0.28.1
```

**Step 2: Verify install**
```bash
cd /Users/kapilsharma/Scanner/backend
pip install httpx==0.28.1
python -c "import httpx; print('OK')"
```
Expected: `OK`

**Step 3: Commit**
```bash
git add backend/requirements.txt
git commit -m "feat: add httpx for OpenFoodFacts API calls"
```

---

## Task 2: Update barcode endpoint to use OpenFoodFacts

**Files:**
- Modify: `backend/server.py`

> **Context:** The existing `get_product_by_barcode` function is at line 368 in `server.py`. It currently returns 404 if the barcode isn't in the DB. We're replacing that 404 with an OpenFoodFacts lookup.
>
> The `generate_brand_with_claude` function and `brand_import_to_db` helper will be added in the brand intelligence plan (Tasks 6-7 of the other plan). For now, if brand isn't in DB, we'll store a minimal brand record and skip the score. Once the other tasks are implemented, the score will appear automatically.
>
> **Important:** `server.py` uses synchronous psycopg2 DB calls but FastAPI is async. Use `httpx.AsyncClient` for OpenFoodFacts calls (non-blocking). The existing DB calls remain synchronous (acceptable for now).

**Step 1: Add `httpx` import at top of `server.py`**

Find the imports section (lines 1-11) and add `httpx`:
```python
from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import json
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
```

**Step 2: Add OpenFoodFacts helper function**

Add this function after the `get_db_connection` context manager (after line 30), before `init_db`:

```python
async def fetch_from_openfoodfacts(barcode: str) -> Optional[dict]:
    """
    Fetch product data from OpenFoodFacts API.
    Returns dict with keys: name, brand_name, category
    Returns None if product not found or API error.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            data = response.json()

        if data.get('status') != 1:
            return None

        product = data.get('product', {})

        # Extract product name
        name = product.get('product_name') or product.get('product_name_en', '')
        if not name:
            return None

        # Extract brand name (first if comma-separated)
        brands_raw = product.get('brands', '')
        brand_name = brands_raw.split(',')[0].strip() if brands_raw else ''
        if not brand_name:
            return None

        # Extract category (strip "en:" prefix)
        categories = product.get('categories_tags', [])
        category = categories[0].replace('en:', '') if categories else 'general'

        return {
            'name': name,
            'brand_name': brand_name,
            'category': category,
        }
    except Exception as e:
        logger.error(f"OpenFoodFacts API error for {barcode}: {e}")
        return None
```

**Step 3: Replace the `get_product_by_barcode` endpoint**

Find and replace the entire `get_product_by_barcode` function (lines 368-389):

Old code:
```python
@api_router.get("/product/barcode/{barcode}")
async def get_product_by_barcode(barcode: str):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT p.id, p.barcode, p.name, p.brand_id, p.category
            FROM products p
            WHERE p.barcode = %s
        """, (barcode,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get brand details
        cursor.execute("SELECT * FROM brands WHERE id = %s", (product['brand_id'],))
        brand = cursor.fetchone()

        result = dict(product)
        result['brand'] = dict(brand) if brand else None

        return result
```

New code:
```python
@api_router.get("/product/barcode/{barcode}")
async def get_product_by_barcode(barcode: str):
    # Step 1: Check DB cache
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT p.id, p.barcode, p.name, p.brand_id, p.category
            FROM products p
            WHERE p.barcode = %s
        """, (barcode,))
        product = cursor.fetchone()

        if product:
            cursor.execute("SELECT * FROM brands WHERE id = %s", (product['brand_id'],))
            brand = cursor.fetchone()
            result = dict(product)
            result['brand'] = dict(brand) if brand else None
            if brand:
                score_data = calculate_india_score(dict(brand))
                result.update(score_data)
            return result

    # Step 2: Not in DB — try OpenFoodFacts
    off_data = await fetch_from_openfoodfacts(barcode)
    if not off_data:
        raise HTTPException(status_code=404, detail="Product not found")

    brand_name = off_data['brand_name']

    # Step 3: Look up or create brand
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM brands WHERE LOWER(brand_name) = LOWER(%s)",
            (brand_name,)
        )
        brand = cursor.fetchone()

        if not brand:
            # Try Claude generation if available, else create minimal record
            if ANTHROPIC_API_KEY:
                try:
                    brand_data = generate_brand_with_claude(brand_name)
                    db_brand = brand_import_to_db(BrandImport(**brand_data))
                except Exception as e:
                    logger.error(f"Claude generation failed for {brand_name}: {e}")
                    db_brand = {
                        'brand_name': brand_name,
                        'parent_company': brand_name,
                        'ownership_country': 'Unknown',
                        'is_indian_company': False,
                        'manufactures_in_india': 'false',
                        'manufacturing_states': [],
                        'employees_in_india_estimate': '0',
                        'data_storage_country': 'Unknown',
                        'security_flags': [],
                        'govt_restrictions': [],
                        'source_links': [],
                    }
            else:
                db_brand = {
                    'brand_name': brand_name,
                    'parent_company': brand_name,
                    'ownership_country': 'Unknown',
                    'is_indian_company': False,
                    'manufactures_in_india': 'false',
                    'manufacturing_states': [],
                    'employees_in_india_estimate': '0',
                    'data_storage_country': 'Unknown',
                    'security_flags': [],
                    'govt_restrictions': [],
                    'source_links': [],
                }

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
            brand_id = cursor.fetchone()['id']
            conn.commit()

            cursor.execute("SELECT * FROM brands WHERE id = %s", (brand_id,))
            brand = cursor.fetchone()

        brand_id = brand['id']

        # Step 4: Cache product in DB
        cursor.execute("""
            INSERT INTO products (barcode, name, brand_id, category)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (barcode) DO NOTHING
            RETURNING id
        """, (barcode, off_data['name'], brand_id, off_data['category']))
        row = cursor.fetchone()
        if row:
            product_id = row['id']
        else:
            cursor.execute("SELECT id FROM products WHERE barcode = %s", (barcode,))
            product_id = cursor.fetchone()['id']
        conn.commit()

        # Step 5: Build and return response
        result = {
            'id': product_id,
            'barcode': barcode,
            'name': off_data['name'],
            'brand_id': brand_id,
            'category': off_data['category'],
            'brand': dict(brand),
        }
        score_data = calculate_india_score(dict(brand))
        result.update(score_data)
        return result
```

**Step 4: Test locally**
```bash
cd /Users/kapilsharma/Scanner/backend
export ANTHROPIC_API_KEY="sk-ant-..."
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

In a second terminal:
```bash
# Test with Parle-G barcode (real product on OpenFoodFacts)
curl -s "http://localhost:8001/api/product/barcode/8901719101038" | python3 -m json.tool
```
Expected: JSON with `name: "Parle-G"`, `brand.brand_name: "Parle"`, `score`, `recommendation`

```bash
# Test with a barcode that doesn't exist anywhere
curl -s "http://localhost:8001/api/product/barcode/0000000000000"
```
Expected: `{"detail": "Product not found"}`

```bash
# Test same barcode again (should be cached now, no OpenFoodFacts call)
curl -s "http://localhost:8001/api/product/barcode/8901719101038" | python3 -m json.tool
```
Expected: same response, faster (from DB cache)

**Step 5: Commit and push**
```bash
git add backend/server.py backend/requirements.txt
git commit -m "feat: integrate OpenFoodFacts API for barcode lookup with Claude brand scoring"
git push origin claude/build-scanner-app-axlSK
```

**Step 6: Deploy to Render**

In Render dashboard → your web service → **Manual Deploy** → **Deploy latest commit**.

Wait for deploy to complete (~2 minutes), then verify:
```bash
curl -s "https://scanner-p49u.onrender.com/api/product/barcode/8901719101038" | python3 -m json.tool
```
Expected: JSON with product name, brand, score, recommendation

---

## Task 3: Verify end-to-end on device

**Steps:**

**Step 1: Wake up Render (free tier sleeps after inactivity)**
```bash
curl -s "https://scanner-p49u.onrender.com/api/"
```
Wait for `{"message":"India First..."}` before testing on device.

**Step 2: Build new APK**
```bash
cd /Users/kapilsharma/Scanner/frontend
npx eas-cli build --platform android --profile preview
```

**Step 3: Install and test**
- Install the new APK on Android device
- Open app → tap the scanner icon
- Scan any real FMCG product barcode (Parle-G, Amul, Colgate, etc.)
- Expected: product name + brand + India Interest Score displayed

**Step 4: Test edge case**
- Scan a barcode that's unlikely to be in DB (random product)
- Expected: either shows result from OpenFoodFacts, or "Product not found" — not a crash
