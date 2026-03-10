# OpenFoodFacts Integration Design

## Goal
Replace hardcoded product DB lookups with OpenFoodFacts API so any real barcode scan returns a product, then automatically generate or look up the brand's India Interest Score.

## Architecture

```
Scan barcode
→ GET /api/product/barcode/{barcode}

Backend:
  1. Check products table → if found, return cached result
  2. Call OpenFoodFacts: GET https://world.openfoodfacts.org/api/v0/product/{barcode}.json
  3. Extract: product_name, brands, categories_tags[0]
  4. Look up brand in brands table
     → found: calculate score from existing data
     → not found: call Claude to generate brand → store → calculate score
  5. Cache product in DB (barcode, name, brand_id, category)
  6. Return combined response: product + brand + score + breakdown

Frontend: no changes needed (scanner.tsx already calls this endpoint)
```

## Response Shape

```json
{
  "id": 42,
  "barcode": "8901719101038",
  "name": "Parle-G Biscuits",
  "brand_id": 2,
  "category": "biscuits",
  "brand": {
    "id": 2,
    "brand_name": "Parle",
    "ownership_country": "India",
    "is_indian_company": true
  },
  "score": 9.5,
  "breakdown": { "indian_ownership": {...}, "manufacturing": {...} },
  "recommendation": "🇮🇳 Strongly Recommended"
}
```

## Data Mapping from OpenFoodFacts

| OpenFoodFacts field | Our DB field |
|---------------------|-------------|
| `product.product_name` | `products.name` |
| `product.brands` (first value if comma-separated) | `brands.brand_name` |
| `product.categories_tags[0]` stripped of `en:` prefix | `products.category` |

## Error Handling

| Situation | Response |
|-----------|----------|
| Not in DB AND not on OpenFoodFacts | 404: "Product not found" |
| OpenFoodFacts returns `status: 0` (not found) | 404: "Product not found" |
| OpenFoodFacts API timeout/error | 503: "Unable to look up product, try again" |
| Brand generation (Claude) fails | Return product + brand name, score omitted |

## Tech Stack
- `httpx` (async HTTP client for OpenFoodFacts calls from FastAPI)
- Existing `anthropic` SDK for brand generation
- Existing PostgreSQL for caching
