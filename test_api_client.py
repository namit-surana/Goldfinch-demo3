#!/usr/bin/env python3
"""
Test Client for TIC Research API
Demonstrates how to use the API with domain metadata and chat history
"""

import requests
import json
import time
from typing import List, Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Sample domain metadata (as provided by user)
DOMAIN_METADATA = [
    {
        "name": "Consumer Product Safety Commission (CPSC)",
        "homepage": "https://www.cpsc.gov",
        "domain": "cpsc.gov",
        "region": "United States",
        "org_type": "Government",
        "aliases": ["CPSC"],
        "industry_tags": ["SafetyRegulator", "ConsumerGoods"],
        "semantic_profile": "The Consumer Product Safety Commission (CPSC) is a U.S. federal agency charged with protecting the public from potential hazards associated with consumer products. The CPSC oversees the regulation of thousands of types of consumer products under its jurisdiction, including toys, cribs, power tools, cigarette lighters, and household chemicals, to ensure they do not pose significant risks of injury or death. Primarily, the CPSC works by enforcing adherence to laws like the Consumer Product Safety Act and Federal Hazardous Substances Act. It conducts product testing, market surveillance, and initiates recalls or bans on non-compliant products. The CPSC also facilitates the creation of voluntary standards and collaborates with corporations for designing safer products. The organization operates primarily within the United States but works alongside international bodies for global product safety enhancements. CPSC's activities include setting mandatory safety standards and conducting compliance verification, and it remains an authoritative entity for product recalls and hazard reports.",
        "boost_keywords": ["consumer safety regulations", "product recall CPSC", "toy safety compliance", "household chemicals regulation", "CPSC product standards", "Federal Hazardous Substances Act enforcement", "CPSC market surveillance", "consumer injury protection", "U.S. product hazard management", "mandatory safety standards for consumer goods", "U.S. product recalls", "consumer product testing CPSC", "CPSC jurisdiction products", "CPSC regulation enforcement", "U.S. federal product safety"]
    },
    {
        "name": "Element Materials Technology",
        "homepage": "https://www.element.com",
        "domain": "element.com",
        "region": "Global",
        "org_type": "Private",
        "aliases": ["Element", "Element MT"],
        "industry_tags": ["StandardsBody", "Electronics", "ConsumerGoods"],
        "semantic_profile": "Element Materials Technology is a global provider specializing in testing, inspection, and certification services. With extensive experience across a wide range of industries, Element serves sectors such as consumer goods, electronics, aerospace, defense, and more. The company offers comprehensive services in material testing, product qualification, and certification. Beyond physical testing, Element ensures compliance with international standards, facilitating market entry through certifications like CE marking, and ensuring products meet the necessary safety and quality benchmarks. Their services support clients seeking conformity assessments and performance evaluations, applying both industry-specific and broad international standards. As a recognized entity in the testing, inspection, and certification (TIC) landscape, Element provides key regulatory compliance solutions, helping businesses meet both compulsory requirements and competitive standards on a global scale.",
        "boost_keywords": ["material testing services", "CE marking certification", "consumer product safety testing", "aerospace product qualification", "Element testing and inspection", "global TIC services", "electronics compliance certification", "defense asset reliability testing", "international standards conformance", "quality benchmarking", "product performance evaluation", "testing services for export compliance", "Element market entry certification", "material analysis service", "safety assessments for consumer goods"]
    },
    {
        "name": "Underwriters Laboratories (UL)",
        "homepage": "https://www.ul.com",
        "domain": "ul.com",
        "region": "Global",
        "org_type": "Private",
        "aliases": ["UL", "Underwriters Laboratories Inc.", "UL Solutions"],
        "industry_tags": ["StandardsBody", "ConsumerGoods", "Electronics"],
        "semantic_profile": "Underwriters Laboratories (UL) is a global safety certification company known for its role in developing and certifying safety standards for products, ranging from consumer goods to complex electronics. Founded over a century ago, UL offers certification services designed to promote safe working and living environments. UL works across multiple sectors, including electronics, transportation, and consumer products, providing testing, certification, validation, and audit services. UL certification marks indicate a product has met rigorous safety standards, instilling trust and ensuring compliance with both national and international regulations. Their services extend globally, working with various multinational accreditation bodies, making them a critical player in international trade and safety regulation. UL certifications often involve multiple phase processes, including product testing, factory inspections, and ongoing compliance audits to ensure sustained product safety and performance.",
        "boost_keywords": ["product safety certification UL", "UL certification process", "electrical product testing UL", "UL mark of safety", "UL listing requirements", "consumer product safety certification", "UL international certification services", "safety compliance for electronics", "UL testing laboratories", "fire safety testing by UL", "global product certification UL", "UL conformity assessment services", "electronics safety standards UL", "consumer goods safety validation", "UL audit and inspection services"]
    }
]

# Sample chat history (as provided by user)
CHAT_HISTORY = [
    {
        "role": "user",
        "content": "who are you"
    },
    {
        "role": "user",
        "content": "what is the weather today in NY"
    },
    {
        "role": "user",
        "content": "can you tell me about details of exporting honey to US"
    },
    {
        "role": "user",
        "content": "can you tell me about details of exporting honey to US"
    },
    {
        "role": "user",
        "content": "what certifications are necessary to import condom to China"
    },
    {
        "role": "user",
        "content": "hi"
    }
]

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def start_research(research_question: str) -> str:
    """Start a research request and return the request ID"""
    print(f"🚀 Starting research: {research_question}")
    
    payload = {
        "research_question": research_question,
        "domain_list_metadata": DOMAIN_METADATA,
        "chat_history": CHAT_HISTORY
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/research", json=payload)
        if response.status_code == 200:
            result = response.json()
            request_id = result["request_id"]
            print(f"✅ Research started successfully")
            print(f"   Request ID: {request_id}")
            print(f"   Status: {result['status']}")
            return request_id
        else:
            print(f"❌ Failed to start research: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error starting research: {e}")
        return None

def check_status(request_id: str) -> Dict[str, Any]:
    """Check the status of a research request"""
    try:
        response = requests.get(f"{API_BASE_URL}/research/{request_id}/status")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None

def get_results(request_id: str) -> Dict[str, Any]:
    """Get the results of a completed research request"""
    try:
        response = requests.get(f"{API_BASE_URL}/research/{request_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get results: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting results: {e}")
        return None

def wait_for_completion(request_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
    """Wait for research to complete and return results"""
    print(f"⏳ Waiting for research to complete...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status = check_status(request_id)
        if status:
            print(f"   Status: {status['status']} - {status['message']}")
            
            if status['status'] in ['completed', 'failed', 'error']:
                print(f"✅ Research finished with status: {status['status']}")
                return get_results(request_id)
        
        time.sleep(5)  # Wait 5 seconds before checking again
    
    print(f"⏰ Timeout waiting for research completion")
    return None

def display_results(results: Dict[str, Any]):
    """Print research results in a formatted way"""
    if not results:
        print("❌ No results to display.")
        return
    
    print("\n============================================================")
    print("📊 RESEARCH RESULTS")
    print("============================================================")
    print(f"Request ID: {results.get('request_id')}")
    print(f"Status: {results.get('status')}")
    print(f"Message: {results.get('message')}")
    print(f"Research Question: {results.get('research_question')}")
    print(f"Workflow Type: {results.get('workflow_type')}")
    print(f"Processing Time: {results.get('processing_time'):.2f} seconds" if results.get('processing_time') else "")
    print(f"Timestamp: {results.get('timestamp')}")
    
    if results.get("execution_summary"):
        summary = results["execution_summary"]
        print("\n📈 Execution Summary:")
        print(f"   Total Time: {summary.get('total_time_seconds'):.2f} seconds")
        print(f"   Total Searches: {summary.get('total_searches')}")
        print(f"   General Searches: {summary.get('general_searches')}")
        print(f"   Domain Searches: {summary.get('domain_searches')}")

    if results.get("query_mappings"):
        print("\n🗺️ Query Mappings:")
        for i, mapping in enumerate(results["query_mappings"], 1):
            print(f"   {i}. Query: {mapping['query'][:50]}...")
            print(f"      Websites: {len(mapping['websites'])} sites")

    if results.get("search_results"):
        print("\n🔍 Search Results:")
        for i, result in enumerate(results["search_results"], 1):
            print(f"   {i}. Type: {result['search_type']}")
            print(f"      Status: {result['status']}")
            print(f"      Query: {result['query'][:60]}...")
            if result['websites']:
                print(f"      Websites: {len(result['websites'])} sites")
    
    print("\n" + "="*50)

def main():
    """Main test function"""
    print("🧪 TIC Research API Test Client")
    print("="*50)
    
    # Test health check
    test_health_check()
    print()
    
    # Test 1: Comprehensive research question
    print("==================== Test 1 ====================")
    question1 = "What certifications are required to export electronics to the US?"
    print(f"Question: {question1}")
    
    request_id1 = start_research(question1)
    if request_id1:
        results1 = wait_for_completion(request_id1)
        if results1:
            display_results(results1)
    
    # Test 2: Specific question
    print("\n==================== Test 2 ====================")
    question2 = "What safety standards apply to consumer products in the EU?"
    print(f"Question: {question2}")
    
    request_id2 = start_research(question2)
    if request_id2:
        results2 = wait_for_completion(request_id2)
        if results2:
            display_results(results2)
    
    # Test 3: UL certification question
    print("\n==================== Test 3 ====================")
    question3 = "How do I get UL certification for my product?"
    print(f"Question: {question3}")
    
    request_id3 = start_research(question3)
    if request_id3:
        results3 = wait_for_completion(request_id3)
        if results3:
            display_results(results3)

if __name__ == "__main__":
    main() 