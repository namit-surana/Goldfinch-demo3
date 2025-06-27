#!/usr/bin/env python3
"""
Test script for database integration
Tests the database service and endpoints
"""

import asyncio
import requests
import json
from datetime import datetime
from database.services.database_service import get_database_service
from database.services.llm_db_service import get_llm_db_service

# API Configuration
API_BASE_URL = "http://localhost:8000"

async def test_database_service():
    """Test the database service directly"""
    print("🧪 Testing Database Service...")
    
    try:
        db_service = get_database_service()
        
        # Test connection
        is_connected = await db_service.test_connection()
        print(f"✅ Database connection: {'Connected' if is_connected else 'Failed'}")
        
        if not is_connected:
            print("❌ Database connection failed. Please check your configuration.")
            return False
        
        # Test session creation
        session_data = await db_service.create_session(
            user_id="test_user_123",
            title="Test Session"
        )
        print(f"✅ Session created: {session_data['session_id']}")
        
        # Test message storage
        message_data = await db_service.store_message(
            session_id=session_data['session_id'],
            role="user",
            content="Hello, this is a test message"
        )
        print(f"✅ Message stored: {message_data['message_id']}")
        
        # Test research request storage
        request_id = await db_service.store_research_request(
            session_id=session_data['session_id'],
            research_question="What certifications are needed for electronics?",
            workflow_type="Provide_a_List",
            domain_metadata={"test": True}
        )
        print(f"✅ Research request stored: {request_id}")
        
        # Test analytics logging
        analytics_id = await db_service.log_analytics_event(
            event_type="test_event",
            event_data={"test": True},
            session_id=session_data['session_id']
        )
        print(f"✅ Analytics event logged: {analytics_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database service test failed: {e}")
        return False

def test_database_endpoints():
    """Test the database endpoints via HTTP"""
    print("\n🌐 Testing Database Endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{API_BASE_URL}/db/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check: {health_data['database']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test session creation endpoint
        session_payload = {
            "user_id": "test_user_456",
            "title": "API Test Session"
        }
        
        response = requests.post(f"{API_BASE_URL}/db/sessions/create", json=session_payload)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session']['session_id']
            print(f"✅ Session created via API: {session_id}")
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            return False
        
        # Test message storage endpoint
        message_payload = {
            "session_id": session_id,
            "role": "user",
            "content": "Hello from API test"
        }
        
        response = requests.post(f"{API_BASE_URL}/db/messages/store", json=message_payload)
        if response.status_code == 200:
            message_data = response.json()
            print(f"✅ Message stored via API: {message_data['message']['message_id']}")
        else:
            print(f"❌ Message storage failed: {response.status_code}")
            return False
        
        # Test research request storage endpoint
        research_payload = {
            "session_id": session_id,
            "enhanced_query": "What are the safety standards for toys?",
            "workflow_type": "Search_the_Internet",
            "domain_metadata": {"test": True}
        }
        
        response = requests.post(f"{API_BASE_URL}/db/research/store", json=research_payload)
        if response.status_code == 200:
            research_data = response.json()
            request_id = research_data['request_id']
            print(f"✅ Research request stored via API: {request_id}")
        else:
            print(f"❌ Research request storage failed: {response.status_code}")
            return False
        
        # Test context retrieval endpoint
        response = requests.get(f"{API_BASE_URL}/db/context/{session_id}")
        if response.status_code == 200:
            context_data = response.json()
            print(f"✅ Context retrieved: {len(context_data['context']['recent_messages'])} messages")
        else:
            print(f"❌ Context retrieval failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database endpoints test failed: {e}")
        return False

async def test_llm_db_integration():
    """Test LLM database integration service"""
    print("\n🤖 Testing LLM Database Integration...")
    
    try:
        llm_db_service = get_llm_db_service()
        
        # Create a test session
        session_data = await llm_db_service.db_service.create_session(
            user_id="llm_test_user",
            title="LLM Integration Test"
        )
        session_id = session_data['session_id']
        
        # Test context retrieval
        context = await llm_db_service.get_research_context(session_id)
        print(f"✅ Research context retrieved: {context['context_summary']['total_messages']} messages")
        
        # Test research workflow integration
        request_id = await llm_db_service.start_research_workflow(
            session_id=session_id,
            research_question="What certifications are needed for medical devices?",
            workflow_type="Provide_a_List",
            domain_metadata={"test": True}
        )
        print(f"✅ Research workflow started: {request_id}")
        
        # Test message storage
        user_message = await llm_db_service.store_user_message(
            session_id=session_id,
            content="What are the requirements for exporting electronics to the EU?"
        )
        print(f"✅ User message stored: {user_message['message_id']}")
        
        assistant_message = await llm_db_service.store_assistant_message(
            session_id=session_id,
            content="I'll help you find the certification requirements for exporting electronics to the EU."
        )
        print(f"✅ Assistant message stored: {assistant_message['message_id']}")
        
        # Test performance logging
        analytics_id = await llm_db_service.log_llm_performance(
            event_type="router_decision",
            performance_data={
                "response_time": 1.5,
                "tokens_used": 150,
                "workflow_selected": "Provide_a_List"
            },
            session_id=session_id
        )
        print(f"✅ Performance logged: {analytics_id}")
        
        # Test session analytics
        analytics = await llm_db_service.get_session_analytics(session_id)
        print(f"✅ Session analytics: {analytics['total_research_requests']} requests")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM database integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Database Integration Tests")
    print("=" * 50)
    
    # Test database service
    db_service_ok = await test_database_service()
    
    # Test database endpoints
    endpoints_ok = test_database_endpoints()
    
    # Test LLM integration
    llm_integration_ok = await test_llm_db_integration()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Database Service: {'✅ PASS' if db_service_ok else '❌ FAIL'}")
    print(f"Database Endpoints: {'✅ PASS' if endpoints_ok else '❌ FAIL'}")
    print(f"LLM Integration: {'✅ PASS' if llm_integration_ok else '❌ FAIL'}")
    
    if all([db_service_ok, endpoints_ok, llm_integration_ok]):
        print("\n🎉 All tests passed! Database integration is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check your configuration and database setup.")

if __name__ == "__main__":
    asyncio.run(main()) 