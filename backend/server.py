from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import httpx
import hmac
import hashlib
import base64
import json
import time

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL connection
POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/india_first')

# GitHub OAuth settings
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')
GITHUB_REDIRECT_URI = os.environ.get('GITHUB_REDIRECT_URI', 'http://localhost:8001/api/auth/github/callback')
FRONTEND_REDIRECT_SCHEME = os.environ.get('FRONTEND_REDIRECT_SCHEME', 'indiafirst')
JWT_SECRET = os.environ.get('JWT_SECRET', 'india-first-jwt-secret-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_DAYS = 30

security = HTTPBearer(auto_error=False)

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Database helper
@contextmanager
def get_db_connection():
    conn = psycopg2.connect(POSTGRES_URL)
    try:
        yield conn
    finally:
        conn.close()

# Initialize database tables
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create brands table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                id SERIAL PRIMARY KEY,
                brand_name VARCHAR(255) UNIQUE NOT NULL,
                parent_company VARCHAR(255),
                ownership_country VARCHAR(100),
                is_indian_company BOOLEAN,
                manufactures_in_india VARCHAR(50),
                manufacturing_states TEXT[],
                employees_in_india_estimate VARCHAR(100),
                data_storage_country VARCHAR(100),
                security_flags TEXT[],
                govt_restrictions TEXT[],
                source_links TEXT[]
            )
        """)
        
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                barcode VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                brand_id INTEGER REFERENCES brands(id),
                category VARCHAR(100)
            )
        """)

        # Create users table for GitHub OAuth
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                github_id INTEGER UNIQUE NOT NULL,
                github_login VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                email VARCHAR(255),
                avatar_url TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        logger.info("Database tables initialized")
        
        # Seed mock data
        seed_mock_data(conn)

def seed_mock_data(conn):
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM brands")
    if cursor.fetchone()[0] > 0:
        logger.info("Mock data already exists")
        return
    
    # Indian brands
    brands_data = [
        {
            'brand_name': 'Amul',
            'parent_company': 'Gujarat Co-operative Milk Marketing Federation',
            'ownership_country': 'India',
            'is_indian_company': True,
            'manufactures_in_india': 'true',
            'manufacturing_states': ['Gujarat', 'Maharashtra', 'Karnataka'],
            'employees_in_india_estimate': '10000+',
            'data_storage_country': 'India',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://amul.com']
        },
        {
            'brand_name': 'Parle',
            'parent_company': 'Parle Products Pvt Ltd',
            'ownership_country': 'India',
            'is_indian_company': True,
            'manufactures_in_india': 'true',
            'manufacturing_states': ['Maharashtra', 'Gujarat', 'Karnataka'],
            'employees_in_india_estimate': '8000+',
            'data_storage_country': 'India',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://parleproducts.com']
        },
        {
            'brand_name': 'Britannia',
            'parent_company': 'Britannia Industries Limited',
            'ownership_country': 'India',
            'is_indian_company': True,
            'manufactures_in_india': 'true',
            'manufacturing_states': ['West Bengal', 'Delhi', 'Maharashtra'],
            'employees_in_india_estimate': '5000+',
            'data_storage_country': 'India',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://britannia.co.in']
        },
        {
            'brand_name': 'Patanjali',
            'parent_company': 'Patanjali Ayurved Limited',
            'ownership_country': 'India',
            'is_indian_company': True,
            'manufactures_in_india': 'true',
            'manufacturing_states': ['Uttarakhand', 'Haryana', 'Assam'],
            'employees_in_india_estimate': '15000+',
            'data_storage_country': 'India',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://patanjaliayurved.net']
        },
        {
            'brand_name': 'Dabur',
            'parent_company': 'Dabur India Ltd',
            'ownership_country': 'India',
            'is_indian_company': True,
            'manufactures_in_india': 'true',
            'manufacturing_states': ['Uttar Pradesh', 'Himachal Pradesh', 'Tamil Nadu'],
            'employees_in_india_estimate': '7000+',
            'data_storage_country': 'India',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://dabur.com']
        },
        # Foreign brands
        {
            'brand_name': 'Nestle',
            'parent_company': 'Nestle S.A.',
            'ownership_country': 'Switzerland',
            'is_indian_company': False,
            'manufactures_in_india': 'partial',
            'manufacturing_states': ['Haryana', 'Karnataka', 'Goa'],
            'employees_in_india_estimate': '8000+',
            'data_storage_country': 'Switzerland',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://nestle.in']
        },
        {
            'brand_name': 'Maggi',
            'parent_company': 'Nestle S.A.',
            'ownership_country': 'Switzerland',
            'is_indian_company': False,
            'manufactures_in_india': 'partial',
            'manufacturing_states': ['Punjab', 'Goa'],
            'employees_in_india_estimate': '5000+',
            'data_storage_country': 'Switzerland',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://maggi.in']
        },
        {
            'brand_name': 'Colgate',
            'parent_company': 'Colgate-Palmolive Company',
            'ownership_country': 'USA',
            'is_indian_company': False,
            'manufactures_in_india': 'partial',
            'manufacturing_states': ['Maharashtra', 'Haryana'],
            'employees_in_india_estimate': '4000+',
            'data_storage_country': 'USA',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://colgatepalmolive.co.in']
        },
        {
            'brand_name': 'Dove',
            'parent_company': 'Unilever',
            'ownership_country': 'UK-Netherlands',
            'is_indian_company': False,
            'manufactures_in_india': 'partial',
            'manufacturing_states': ['Maharashtra', 'Uttar Pradesh'],
            'employees_in_india_estimate': '6000+',
            'data_storage_country': 'UK',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://unilever.in']
        },
        {
            'brand_name': 'Coca-Cola',
            'parent_company': 'The Coca-Cola Company',
            'ownership_country': 'USA',
            'is_indian_company': False,
            'manufactures_in_india': 'partial',
            'manufacturing_states': ['Karnataka', 'Haryana', 'Maharashtra'],
            'employees_in_india_estimate': '25000+',
            'data_storage_country': 'USA',
            'security_flags': [],
            'govt_restrictions': [],
            'source_links': ['https://coca-colaindia.com']
        }
    ]
    
    for brand in brands_data:
        cursor.execute("""
            INSERT INTO brands (brand_name, parent_company, ownership_country, is_indian_company,
                              manufactures_in_india, manufacturing_states, employees_in_india_estimate,
                              data_storage_country, security_flags, govt_restrictions, source_links)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (brand_name) DO NOTHING
        """, (
            brand['brand_name'], brand['parent_company'], brand['ownership_country'],
            brand['is_indian_company'], brand['manufactures_in_india'], brand['manufacturing_states'],
            brand['employees_in_india_estimate'], brand['data_storage_country'],
            brand['security_flags'], brand['govt_restrictions'], brand['source_links']
        ))
    
    # Products data
    products_data = [
        {'barcode': '8901058851236', 'name': 'Amul Butter 500g', 'brand': 'Amul', 'category': 'Food & Beverages'},
        {'barcode': '8901719101038', 'name': 'Parle-G Biscuits', 'brand': 'Parle', 'category': 'Snacks'},
        {'barcode': '8901063101210', 'name': 'Britannia Good Day', 'brand': 'Britannia', 'category': 'Snacks'},
        {'barcode': '8904109400018', 'name': 'Patanjali Ghee 1L', 'brand': 'Patanjali', 'category': 'Food & Beverages'},
        {'barcode': '8901207014710', 'name': 'Dabur Honey 500g', 'brand': 'Dabur', 'category': 'Food & Beverages'},
        {'barcode': '8901058847680', 'name': 'Nestle Maggi Noodles', 'brand': 'Maggi', 'category': 'Food & Beverages'},
        {'barcode': '8901396301011', 'name': 'Colgate Toothpaste', 'brand': 'Colgate', 'category': 'Personal Care'},
        {'barcode': '8901525002344', 'name': 'Dove Soap', 'brand': 'Dove', 'category': 'Personal Care'},
        {'barcode': '5449000000996', 'name': 'Coca-Cola 500ml', 'brand': 'Coca-Cola', 'category': 'Food & Beverages'},
    ]
    
    for product in products_data:
        cursor.execute("SELECT id FROM brands WHERE brand_name = %s", (product['brand'],))
        brand_row = cursor.fetchone()
        if brand_row:
            brand_id = brand_row[0]
            cursor.execute("""
                INSERT INTO products (barcode, name, brand_id, category)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (barcode) DO NOTHING
            """, (product['barcode'], product['name'], brand_id, product['category']))
    
    conn.commit()
    logger.info("Mock data seeded successfully")

# Auth helpers — simple HMAC-HS256 JWT using stdlib (avoids cryptography pkg conflicts)
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + '=' * (padding % 4))

def create_jwt_token(user_id: int, github_login: str) -> str:
    header = _b64url_encode(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode())
    payload = _b64url_encode(json.dumps({
        'sub': str(user_id),
        'github_login': github_login,
        'iat': int(time.time()),
        'exp': int(time.time()) + (JWT_EXPIRY_DAYS * 24 * 60 * 60),
    }).encode())
    signing_input = f"{header}.{payload}"
    sig = _b64url_encode(
        hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    )
    return f"{signing_input}.{sig}"

def decode_jwt_token(token: str) -> Optional[dict]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = _b64url_encode(
            hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig_b64, expected_sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if payload.get('exp', 0) < int(time.time()):
            return None  # expired
        return payload
    except Exception:
        return None

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        return None
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE id = %s", (int(payload['sub']),))
        user = cursor.fetchone()
        return dict(user) if user else None

# Models
class UserResponse(BaseModel):
    id: int
    github_id: int
    github_login: str
    name: Optional[str]
    email: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]

class BrandResponse(BaseModel):
    id: int
    brand_name: str
    parent_company: Optional[str]
    ownership_country: Optional[str]
    is_indian_company: Optional[bool]
    manufactures_in_india: Optional[str]
    manufacturing_states: Optional[List[str]]
    employees_in_india_estimate: Optional[str]
    data_storage_country: Optional[str]
    security_flags: Optional[List[str]]
    govt_restrictions: Optional[List[str]]
    source_links: Optional[List[str]]

class ProductResponse(BaseModel):
    id: int
    barcode: str
    name: str
    brand_id: int
    category: Optional[str]
    brand: Optional[BrandResponse]

class ScoreResponse(BaseModel):
    score: float
    breakdown: dict
    recommendation: str

# Calculate India Interest Score
def calculate_india_score(brand: dict) -> dict:
    score = 0.0
    breakdown = {}
    
    # Indian Company (30%)
    if brand.get('is_indian_company'):
        score += 30
        breakdown['indian_ownership'] = {'points': 30, 'max': 30, 'status': 'Indian Company'}
    else:
        breakdown['indian_ownership'] = {'points': 0, 'max': 30, 'status': 'Foreign Company'}
    
    # Manufacturing in India (25%)
    manufacturing = brand.get('manufactures_in_india', 'false')
    if manufacturing == 'true':
        score += 25
        breakdown['manufacturing'] = {'points': 25, 'max': 25, 'status': 'Fully in India'}
    elif manufacturing == 'partial':
        score += 15
        breakdown['manufacturing'] = {'points': 15, 'max': 25, 'status': 'Partially in India'}
    else:
        breakdown['manufacturing'] = {'points': 0, 'max': 25, 'status': 'Not in India'}
    
    # Country relationship (20%)
    friendly_countries = ['India', 'Japan', 'USA', 'France', 'UK', 'Germany', 'Israel', 'UAE']
    country = brand.get('ownership_country', '')
    if country == 'India':
        score += 20
        breakdown['country_relations'] = {'points': 20, 'max': 20, 'status': 'India'}
    elif any(fc in country for fc in friendly_countries):
        score += 12
        breakdown['country_relations'] = {'points': 12, 'max': 20, 'status': f'Friendly ({country})'}
    else:
        score += 5
        breakdown['country_relations'] = {'points': 5, 'max': 20, 'status': f'Neutral ({country})'}
    
    # Employment in India (15%)
    emp = brand.get('employees_in_india_estimate', '')
    if '15000' in emp or '25000' in emp:
        score += 15
        breakdown['employment'] = {'points': 15, 'max': 15, 'status': f'{emp} jobs'}
    elif '10000' in emp or '8000' in emp:
        score += 12
        breakdown['employment'] = {'points': 12, 'max': 15, 'status': f'{emp} jobs'}
    elif '5000' in emp or '4000' in emp:
        score += 8
        breakdown['employment'] = {'points': 8, 'max': 15, 'status': f'{emp} jobs'}
    else:
        score += 5
        breakdown['employment'] = {'points': 5, 'max': 15, 'status': 'Limited jobs'}
    
    # Data storage (10%)
    data_country = brand.get('data_storage_country', '')
    if data_country == 'India':
        score += 10
        breakdown['data_sovereignty'] = {'points': 10, 'max': 10, 'status': 'India'}
    else:
        breakdown['data_sovereignty'] = {'points': 0, 'max': 10, 'status': f'Stored in {data_country}'}
    
    # Normalize to 1-10
    final_score = (score / 100) * 10
    
    # Recommendation
    if final_score >= 8:
        recommendation = '🇮🇳 Strongly Recommended - Great for India!'
    elif final_score >= 6:
        recommendation = '✅ Recommended - Good for India'
    elif final_score >= 4:
        recommendation = '⚠️ Neutral - Consider alternatives'
    else:
        recommendation = '❌ Not Recommended - Look for Indian brands'
    
    return {
        'score': round(final_score, 1),
        'breakdown': breakdown,
        'recommendation': recommendation
    }

# Routes
@api_router.get("/")
async def root():
    return {"message": "India First - FMCG Intelligence API", "version": "1.0"}

# GitHub OAuth routes
@api_router.get("/auth/github")
async def github_auth():
    """Redirect user to GitHub OAuth authorization page."""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID.")
    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
    )
    return RedirectResponse(url=github_url)

@api_router.get("/auth/github/callback")
async def github_callback(code: str):
    """Handle GitHub OAuth callback, exchange code for user info, issue JWT."""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured.")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_response.json()

    access_token = token_data.get("access_token")
    if not access_token:
        error = token_data.get("error_description", "Failed to obtain access token")
        return RedirectResponse(url=f"{FRONTEND_REDIRECT_SCHEME}://auth/callback?error={error}")

    # Fetch GitHub user profile
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        github_user = user_response.json()

    github_id = github_user.get("id")
    if not github_id:
        return RedirectResponse(url=f"{FRONTEND_REDIRECT_SCHEME}://auth/callback?error=Failed+to+fetch+user+profile")

    # Upsert user in database
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            INSERT INTO users (github_id, github_login, name, email, avatar_url, bio, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (github_id) DO UPDATE SET
                github_login = EXCLUDED.github_login,
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                avatar_url = EXCLUDED.avatar_url,
                bio = EXCLUDED.bio,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, github_login
        """, (
            github_id,
            github_user.get("login"),
            github_user.get("name"),
            github_user.get("email"),
            github_user.get("avatar_url"),
            github_user.get("bio"),
        ))
        user_row = cursor.fetchone()
        conn.commit()

    jwt_token = create_jwt_token(user_row["id"], user_row["github_login"])
    return RedirectResponse(url=f"{FRONTEND_REDIRECT_SCHEME}://auth/callback?token={jwt_token}")

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user

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

@api_router.get("/brand/{brand_id}", response_model=BrandResponse)
async def get_brand(brand_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM brands WHERE id = %s", (brand_id,))
        brand = cursor.fetchone()
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        return dict(brand)

@api_router.get("/search/brands")
async def search_brands(q: str):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM brands 
            WHERE LOWER(brand_name) LIKE LOWER(%s) 
            OR LOWER(parent_company) LIKE LOWER(%s)
            LIMIT 20
        """, (f'%{q}%', f'%{q}%'))
        brands = cursor.fetchall()
        return [dict(b) for b in brands]

@api_router.get("/search/products")
async def search_products(q: str):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT p.*, b.brand_name
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE LOWER(p.name) LIKE LOWER(%s) OR LOWER(b.brand_name) LIKE LOWER(%s)
            LIMIT 20
        """, (f'%{q}%', f'%{q}%'))
        products = cursor.fetchall()
        return [dict(p) for p in products]

@api_router.get("/score/{brand_id}", response_model=ScoreResponse)
async def get_brand_score(brand_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM brands WHERE id = %s", (brand_id,))
        brand = cursor.fetchone()
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        score_data = calculate_india_score(dict(brand))
        return score_data

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")
