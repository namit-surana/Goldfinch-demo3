#!/usr/bin/env python3
"""
Test script for cancellation functionality
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

async def test_cancellation():
    """Test the cancellation functionality"""
    
    # Test configuration
    base_url = "http://localhost:8000"
    session_id = f"test_session_{int(time.time())}"
    
    print(f"Testing cancellation with session_id: {session_id}")
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Test health check
        print("\n1. Testing health check...")
        async with session.get(f"{base_url}/health") as response:
            if response.status == 200:
                print("✓ Health check passed")
            else:
                print(f"✗ Health check failed: {response.status}")
                return
        
        # 2. Send a chat message
        print("\n2. Sending chat message...")
        chat_data = {
            "session_id": session_id,
            "content": "What are the latest developments in AI technology?"
        }
        
        async with session.post(f"{base_url}/chat/stream_summary", json=chat_data) as response:
            if response.status != 200:
                print(f"✗ Chat request failed: {response.status}")
                return
            
            print("✓ Chat request started")
            
            # Read the first few chunks to get the message_id
            message_id = None
            chunk_count = 0
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        chunk_count += 1
                        
                        if data.get('type') == 'user_message':
                            message_id = data.get('data', {}).get('message_id')
                            print(f"✓ Got message_id: {message_id}")
                            break
                        
                        if chunk_count > 5:  # Limit initial chunks
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            if not message_id:
                print("✗ Could not get message_id")
                return
        
        # 3. Cancel the message
        print(f"\n3. Cancelling message {message_id}...")
        cancel_data = {
            "message_id": message_id,
            "reason": "Test cancellation"
        }
        
        async with session.post(f"{base_url}/chat/cancel", json=cancel_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✓ Cancellation successful: {result}")
            else:
                print(f"✗ Cancellation failed: {response.status}")
                return
        
        # 4. Wait a moment and check if cancellation message was stored
        print("\n4. Waiting for cancellation to take effect...")
        await asyncio.sleep(2)
        
        # 5. Send another message to trigger the cancellation check
        print("\n5. Sending another message to trigger cancellation check...")
        chat_data2 = {
            "session_id": session_id,
            "content": "This should show the cancellation message"
        }
        
        async with session.post(f"{base_url}/chat/stream_summary", json=chat_data2) as response:
            if response.status != 200:
                print(f"✗ Second chat request failed: {response.status}")
                return
            
            print("✓ Second chat request started")
            
            # Look for cancellation message
            found_cancellation = False
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        
                        if data.get('type') == 'cancelled':
                            print(f"✓ Found cancellation message: {data.get('message')}")
                            if data.get('assistant_message'):
                                print(f"✓ Cancellation message stored in database: {data['assistant_message']['message_id']}")
                                found_cancellation = True
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            if not found_cancellation:
                print("✗ No cancellation message found")
        
        print("\n✓ Cancellation test completed!")

if __name__ == "__main__":
    asyncio.run(test_cancellation()) 