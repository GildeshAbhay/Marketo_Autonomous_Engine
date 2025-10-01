#!/usr/bin/env python3
"""
Proper test for Web Search Agent using A2A SDK

Usage: python test.py
"""

import asyncio
import httpx
import json
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import SendMessageRequest, MessageSendParams

async def test_agent():
    print("=" * 60)
    print("Web Search Agent Test (Using A2A SDK)")
    print("=" * 60)
    
    agent_url = "http://localhost:10003"
    
    async with httpx.AsyncClient(timeout=60) as client:
        # Test 1: Get Agent Card
        print("\n1️⃣  Retrieving agent card...")
        card_resolver = A2ACardResolver(client, agent_url)
        
        try:
            agent_card = await card_resolver.get_agent_card()
            print(f"✅ Agent card retrieved!")
            print(f"   Name: {agent_card.name}")
            print(f"   Description: {agent_card.description}")
            print(f"   Skills: {[skill.name for skill in agent_card.skills]}")
        except Exception as e:
            print(f"❌ Failed to get agent card: {e}")
            return
        
        # Test 2: Send Message using A2A Client
        print("\n2️⃣  Sending message using A2A protocol...")
        
        a2a_client = A2AClient(client, agent_card, url=agent_url)
        
        # Don't provide taskId and contextId for the first message
        # Let the server generate them
        message_payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "tell me about Grazitti Interactive"}],
                "messageId": "test-msg-001",
            }
        }
        
        # Create proper SendMessageRequest
        message_request = SendMessageRequest(
            id="test-msg-001",
            params=MessageSendParams.model_validate(message_payload)
        )
        
        try:
            print("   📤 Sending message...")
            # Send message
            response = await a2a_client.send_message(message_request)
            
            print("✅ Message sent successfully!")
            print(f"\nResponse type: {type(response.root)}")
            
            # Parse response
            if hasattr(response.root, 'result'):
                task_result = response.root.result
                
                print(f"\n📊 Task Details:")
                print(f"   Task ID: {task_result.id}")  # FIXED
                print(f"   Context ID: {task_result.context_id}")  # FIXED
                print(f"   State: {task_result.status.state}")  # FIXED
                
                if hasattr(task_result, 'artifacts') and task_result.artifacts:
                    print(f"\n💬 Agent Response:")
                    for artifact in task_result.artifacts:
                        if hasattr(artifact, 'parts'):
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    response_text = part.root.text
                                    # Show first 500 chars
                                    if len(response_text) > 500:
                                        print(f"\n{response_text[:500]}...")
                                        print(f"\n[Response truncated - Total length: {len(response_text)} chars]")
                                    else:
                                        print(f"\n{response_text}")
                else:
                    print("\n⚠️  No artifacts in response yet")
                    print("   The task might still be processing.")
            elif hasattr(response.root, 'error'):
                print(f"\n❌ Error from agent:")
                print(f"   Code: {response.root.error.code}")
                print(f"   Message: {response.root.error.message}")
            else:
                print(f"\n⚠️  Unexpected response structure: {response}")
            
            print("\n" + "=" * 60)
            print("🎉 Test completed successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error sending message: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())