#!/usr/bin/env python3
"""
Test script to demonstrate structured output from OpenAI and Perplexity APIs
"""

import asyncio
import json
from datetime import datetime
from openai import OpenAI
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Pydantic models for structured output
from pydantic import BaseModel
from typing import List

class QueryMapping(BaseModel):
    query: str
    websites: List[str]

class ResearchQueries(BaseModel):
    queries: List[str]

class QueryMappings(BaseModel):
    mappings: List[QueryMapping]

class Certification(BaseModel):
    certificate_name: str
    certificate_description: str
    legal_regulation: str
    legal_text_excerpt: str
    legal_text_meaning: str
    registration_fee: str
    is_required: bool

class Certifications(BaseModel):
    certifications: List[Certification]

async def test_openai_structured_output():
    """Test OpenAI structured output for query generation"""
    print("=" * 80)
    print("🔍 TESTING OPENAI STRUCTURED OUTPUT")
    print("=" * 80)
    
    client = OpenAI()
    
    # Test query generation
    query_generation_prompt = """
    You are a TIC (Testing, Inspection, Certification) research expert. 
    Generate 3-5 comprehensive search queries for the given research question.
    Focus on different aspects: regulatory requirements, certification bodies, testing procedures, and compliance standards.
    
    Return ONLY a JSON object with a "queries" array containing the search queries.
    """
    
    research_question = "What certifications are needed for exporting electrical equipment to the European Union?"
    
    try:
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": query_generation_prompt},
                {"role": "user", "content": f"Research Question: {research_question}"}
            ],
            text_format=ResearchQueries
        )
        
        print(f"📝 Research Question: {research_question}")
        print(f"✅ Generated {len(response.output_parsed.queries)} queries:")
        print()
        
        for i, query in enumerate(response.output_parsed.queries, 1):
            print(f"  {i}. {query}")
        
        print()
        print("🔧 Raw Pydantic Model:")
        print(json.dumps(response.output_parsed.dict(), indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_openai_query_mapping():
    """Test OpenAI structured output for query mapping"""
    print("\n" + "=" * 80)
    print("🗺️  TESTING OPENAI QUERY MAPPING")
    print("=" * 80)
    
    client = OpenAI()
    
    # Test query mapping
    mapping_prompt = """
    You are a TIC research expert. Map the given queries to the most relevant TIC websites.
    Consider the website's specialization, region, and expertise when making mappings.
    
    Available websites:
    - tuv.com (TÜV SÜD - German certification body)
    - bsi-group.com (British Standards Institution)
    - ul.com (Underwriters Laboratories - US safety testing)
    - cpsc.gov (Consumer Product Safety Commission - US)
    - ce-marking.org (CE Marking information portal)
    
    Return ONLY a JSON object with a "mappings" array containing query-website mappings.
    """
    
    queries = [
        "EU electrical equipment safety standards",
        "CE marking requirements for electronics",
        "US product safety testing procedures"
    ]
    
    try:
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": mapping_prompt},
                {"role": "user", "content": f"Queries to map:\n" + "\n".join([f"{i+1}. {query}" for i, query in enumerate(queries)])}
            ],
            text_format=QueryMappings
        )
        
        print(f"📝 Queries to map:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
        print()
        
        print("🗺️  Mappings:")
        for mapping in response.output_parsed.mappings:
            print(f"  Query: {mapping.query}")
            print(f"  Websites: {', '.join(mapping.websites)}")
            print()
        
        print("🔧 Raw Pydantic Model:")
        print(json.dumps(response.output_parsed.dict(), indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_perplexity_structured_output():
    """Test Perplexity structured output"""
    print("\n" + "=" * 80)
    print("🔍 TESTING PERPLEXITY STRUCTURED OUTPUT")
    print("=" * 80)
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ PERPLEXITY_API_KEY not found in environment")
        return
    
    url = "https://api.perplexity.ai/chat/completions"
    
    # Test Perplexity with structured output
    system_prompt = """
    You are a TIC research expert. Find information about certifications and regulatory requirements.
    Return the information in a structured format with the following fields for each certification:
    - certificate_name: Name of the certification
    - certificate_description: Brief description
    - legal_regulation: Governing regulation or standard
    - legal_text_excerpt: Relevant excerpt from regulation
    - legal_text_meaning: Explanation of the legal text
    - registration_fee: Cost information
    - is_required: Whether it's mandatory
    
    Return ONLY a JSON object with a "certifications" array.
    """
    
    query = "What certifications are required for exporting electrical equipment to the European Union?"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    body = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        "temperature": 0.1,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"schema": Certifications.schema()}
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as response:
                data = await response.json()
                
                if response.status == 200:
                    content = data['choices'][0]['message']['content']
                    citations = data.get('citations', [])
                    
                    print(f"📝 Query: {query}")
                    print(f"📊 Citations found: {len(citations)}")
                    print()
                    
                    # Parse with Pydantic
                    parsed_data = json.loads(content)
                    certifications = Certifications(**parsed_data)
                    
                    print("🏆 Certifications found:")
                    for i, cert in enumerate(certifications.certifications, 1):
                        print(f"\n  {i}. {cert.certificate_name}")
                        print(f"     Description: {cert.certificate_description}")
                        print(f"     Regulation: {cert.legal_regulation}")
                        print(f"     Required: {'Yes' if cert.is_required else 'No'}")
                        print(f"     Fee: {cert.registration_fee}")
                    
                    print("\n🔧 Raw Pydantic Model:")
                    print(json.dumps(certifications.dict(), indent=2))
                    
                    if citations:
                        print(f"\n📚 Citations:")
                        for i, citation in enumerate(citations, 1):
                            if isinstance(citation, dict):
                                print(f"  {i}. {citation.get('title', 'No title')}")
                                print(f"     URL: {citation.get('url', 'No URL')}")
                            else:
                                print(f"  {i}. {citation}")
                else:
                    print(f"❌ API Error: {response.status}")
                    print(data)
                    
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Run all structured output tests"""
    print("🚀 TESTING STRUCTURED OUTPUT FEATURES")
    print("=" * 80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test OpenAI structured output
    await test_openai_structured_output()
    
    # Test OpenAI query mapping
    await test_openai_query_mapping()
    
    # Test Perplexity structured output
    await test_perplexity_structured_output()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 