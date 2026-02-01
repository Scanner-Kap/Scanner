from fastapi import FastAPI, APIRouter, HTTPException
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL connection
POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/india_first')

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

# Models
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

@api_router.get("/product/barcode/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(barcode: str):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT p.*, 
                   b.id as brand_id, b.brand_name, b.parent_company, b.ownership_country,
                   b.is_indian_company, b.manufactures_in_india, b.manufacturing_states,
                   b.employees_in_india_estimate, b.data_storage_country, b.security_flags,
                   b.govt_restrictions, b.source_links
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE p.barcode = %s
        """, (barcode,))
        product = cursor.fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return dict(product)

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
