#!/usr/bin/env python3
"""
Backend API Testing for India First FMCG Product Intelligence App
Tests all API endpoints with comprehensive validation
"""

import requests
import json
import sys
from typing import Dict, Any

# Backend URL from frontend .env
BASE_URL = "https://makeininda.preview.emergentagent.com/api"

class APITester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                     description: str = "", validate_func=None) -> Dict[str, Any]:
        """Test a single API endpoint"""
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🧪 Testing: {description}")
        print(f"   {method} {url}")
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            print(f"   Status: {response.status_code}")
            
            # Check status code
            if response.status_code != expected_status:
                print(f"   ❌ FAILED: Expected {expected_status}, got {response.status_code}")
                self.failed += 1
                result = {
                    "endpoint": endpoint,
                    "description": description,
                    "status": "FAILED",
                    "error": f"Status code {response.status_code} != {expected_status}",
                    "response": response.text[:500] if response.text else None
                }
                self.results.append(result)
                return result
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"   ❌ FAILED: Invalid JSON response")
                self.failed += 1
                result = {
                    "endpoint": endpoint,
                    "description": description,
                    "status": "FAILED",
                    "error": "Invalid JSON response",
                    "response": response.text[:500]
                }
                self.results.append(result)
                return result
            
            # Custom validation
            if validate_func:
                validation_result = validate_func(data)
                if validation_result != True:
                    print(f"   ❌ FAILED: {validation_result}")
                    self.failed += 1
                    result = {
                        "endpoint": endpoint,
                        "description": description,
                        "status": "FAILED",
                        "error": validation_result,
                        "response": data
                    }
                    self.results.append(result)
                    return result
            
            print(f"   ✅ PASSED")
            self.passed += 1
            result = {
                "endpoint": endpoint,
                "description": description,
                "status": "PASSED",
                "response": data
            }
            self.results.append(result)
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ FAILED: Network error - {str(e)}")
            self.failed += 1
            result = {
                "endpoint": endpoint,
                "description": description,
                "status": "FAILED",
                "error": f"Network error: {str(e)}"
            }
            self.results.append(result)
            return result
    
    def validate_health_check(self, data):
        """Validate health check response"""
        if not isinstance(data, dict):
            return "Response is not a dictionary"
        if "message" not in data:
            return "Missing 'message' field"
        if "version" not in data:
            return "Missing 'version' field"
        return True
    
    def validate_product_response(self, data):
        """Validate product response structure"""
        if not isinstance(data, dict):
            return "Response is not a dictionary"
        
        required_fields = ["id", "barcode", "name", "brand_id", "brand"]
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"
        
        # Validate brand nested object
        brand = data.get("brand")
        if not isinstance(brand, dict):
            return "Brand field is not a dictionary"
        
        brand_fields = ["id", "brand_name", "parent_company", "ownership_country", 
                       "is_indian_company", "manufactures_in_india"]
        for field in brand_fields:
            if field not in brand:
                return f"Missing brand field: {field}"
        
        return True
    
    def validate_brand_response(self, data):
        """Validate brand response structure"""
        if not isinstance(data, dict):
            return "Response is not a dictionary"
        
        required_fields = ["id", "brand_name", "parent_company", "ownership_country",
                          "is_indian_company", "manufactures_in_india", "manufacturing_states",
                          "employees_in_india_estimate", "data_storage_country"]
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"
        
        return True
    
    def validate_score_response(self, data):
        """Validate score response structure"""
        if not isinstance(data, dict):
            return "Response is not a dictionary"
        
        required_fields = ["score", "breakdown", "recommendation"]
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"
        
        # Validate score range
        score = data.get("score")
        if not isinstance(score, (int, float)) or score < 1 or score > 10:
            return f"Score {score} is not between 1-10"
        
        # Validate breakdown structure
        breakdown = data.get("breakdown")
        if not isinstance(breakdown, dict):
            return "Breakdown is not a dictionary"
        
        expected_categories = ["indian_ownership", "manufacturing", "country_relations", 
                             "employment", "data_sovereignty"]
        for category in expected_categories:
            if category not in breakdown:
                return f"Missing breakdown category: {category}"
            
            cat_data = breakdown[category]
            if not isinstance(cat_data, dict):
                return f"Category {category} is not a dictionary"
            
            if "points" not in cat_data or "max" not in cat_data or "status" not in cat_data:
                return f"Category {category} missing required fields"
        
        return True
    
    def validate_search_response(self, data):
        """Validate search response structure"""
        if not isinstance(data, list):
            return "Response is not a list"
        return True
    
    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🚀 Starting India First FMCG API Tests")
        print("=" * 60)
        
        # 1. Health Check
        self.test_endpoint("GET", "/", 200, 
                          "Health check endpoint", 
                          self.validate_health_check)
        
        # 2. Product by Barcode Tests
        # Test with Amul Butter
        self.test_endpoint("GET", "/product/barcode/8901058851236", 200,
                          "Get Amul Butter by barcode",
                          self.validate_product_response)
        
        # Test with Parle-G
        self.test_endpoint("GET", "/product/barcode/8901719101038", 200,
                          "Get Parle-G by barcode",
                          self.validate_product_response)
        
        # Test with Coca-Cola
        self.test_endpoint("GET", "/product/barcode/5449000000996", 200,
                          "Get Coca-Cola by barcode",
                          self.validate_product_response)
        
        # Test with invalid barcode
        self.test_endpoint("GET", "/product/barcode/invalid123", 404,
                          "Get product with invalid barcode")
        
        # 3. Brand Details Tests
        # Test with Amul (Indian brand)
        self.test_endpoint("GET", "/brand/1", 200,
                          "Get Amul brand details",
                          self.validate_brand_response)
        
        # Test with Nestle (Foreign brand)
        self.test_endpoint("GET", "/brand/6", 200,
                          "Get Nestle brand details",
                          self.validate_brand_response)
        
        # Test with invalid brand_id
        self.test_endpoint("GET", "/brand/999", 404,
                          "Get brand with invalid ID")
        
        # 4. Score Calculation Tests
        # Test Amul score (should be high ~9-10)
        amul_score = self.test_endpoint("GET", "/score/1", 200,
                                       "Calculate Amul India Interest Score",
                                       self.validate_score_response)
        
        # Validate Amul score is high
        if amul_score.get("status") == "PASSED":
            score = amul_score["response"]["score"]
            if score < 8:
                print(f"   ⚠️  WARNING: Amul score {score} is lower than expected (should be 8+)")
        
        # Test Nestle score (should be medium ~5-7)
        nestle_score = self.test_endpoint("GET", "/score/6", 200,
                                         "Calculate Nestle India Interest Score",
                                         self.validate_score_response)
        
        # Validate Nestle score is medium
        if nestle_score.get("status") == "PASSED":
            score = nestle_score["response"]["score"]
            if score < 4 or score > 8:
                print(f"   ⚠️  WARNING: Nestle score {score} outside expected range (4-8)")
        
        # Test invalid brand score
        self.test_endpoint("GET", "/score/999", 404,
                          "Calculate score for invalid brand")
        
        # 5. Brand Search Tests
        self.test_endpoint("GET", "/search/brands?q=Amul", 200,
                          "Search brands for 'Amul'",
                          self.validate_search_response)
        
        self.test_endpoint("GET", "/search/brands?q=Nestle", 200,
                          "Search brands for 'Nestle'",
                          self.validate_search_response)
        
        # Test case-insensitive search
        self.test_endpoint("GET", "/search/brands?q=amul", 200,
                          "Search brands for 'amul' (lowercase)",
                          self.validate_search_response)
        
        # Test no results
        self.test_endpoint("GET", "/search/brands?q=xyz123", 200,
                          "Search brands for non-existent brand",
                          self.validate_search_response)
        
        # 6. Product Search Tests
        self.test_endpoint("GET", "/search/products?q=Butter", 200,
                          "Search products for 'Butter'",
                          self.validate_search_response)
        
        self.test_endpoint("GET", "/search/products?q=Maggi", 200,
                          "Search products for 'Maggi'",
                          self.validate_search_response)
        
        # Test case-insensitive search
        self.test_endpoint("GET", "/search/products?q=butter", 200,
                          "Search products for 'butter' (lowercase)",
                          self.validate_search_response)
        
        # Test no results
        self.test_endpoint("GET", "/search/products?q=nonexistent", 200,
                          "Search products for non-existent product",
                          self.validate_search_response)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        
        # Print failed tests details
        if self.failed > 0:
            print("\n🔍 FAILED TESTS DETAILS:")
            print("-" * 40)
            for result in self.results:
                if result["status"] == "FAILED":
                    print(f"❌ {result['description']}")
                    print(f"   Endpoint: {result['endpoint']}")
                    print(f"   Error: {result['error']}")
                    if result.get('response'):
                        print(f"   Response: {str(result['response'])[:200]}...")
                    print()
        
        return self.failed == 0

def main():
    """Main test runner"""
    tester = APITester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()