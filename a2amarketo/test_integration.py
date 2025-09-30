#!/usr/bin/env python3
"""
Integration test script to verify A2A communication between host agent and Marketo agent.

Usage:
    python test_integration.py

Make sure all three services are running:
1. MCP Server: python -m mcp-servers.marketo_server (from marketo_agent directory)
2. Marketo Agent: uv run --active . (from marketo_agent directory) 
3. Host Agent: uv run --active adk web (from host_agent_marketo directory)
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_agent_card_retrieval():
    """Test that we can retrieve the agent card from the Marketo agent."""
    print("Testing agent card retrieval...")
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get("http://localhost:10002/.well-known/agent-card.json")
            if response.status_code == 200:
                card_data = response.json()
                print(f"✅ Agent card retrieved successfully:")
                print(f"   Name: {card_data.get('name')}")
                print(f"   Description: {card_data.get('description')}")
                print(f"   Skills: {[skill.get('name') for skill in card_data.get('skills', [])]}")
                return True
            else:
                print(f"❌ Failed to retrieve agent card. Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error retrieving agent card: {e}")
            return False

async def test_mcp_server():
    """Test that the MCP server is responding."""
    print("\nTesting MCP server connectivity...")
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get("http://localhost:8002/sse")
            if response.status_code in [200, 405]:  # 405 is expected for GET on SSE endpoint
                print("✅ MCP server is responding")
                return True
            else:
                print(f"❌ MCP server returned unexpected status: {response.status_code}")
                print(f"Response text: {response.text}")
                return False
        except httpx.ConnectError as e:
            print(f"❌ Cannot connect to MCP server: {e}")
            print("Make sure MCP server is running: python -m mcp-servers.marketo_server")
            return False
        except Exception as e:
            print(f"❌ Error connecting to MCP server: {e}")
            return False

async def test_host_agent():
    """Test that the host agent is responding."""
    print("\nTesting host agent connectivity...")
    
    async with httpx.AsyncClient(timeout=10) as client:
        # Try both common ADK ports
        ports = [8000, 8080]
        for port in ports:
            try:
                response = await client.get(f"http://localhost:{port}")
                if response.status_code == 200:
                    print(f"✅ Host agent web interface is accessible on port {port}")
                    return True
                else:
                    print(f"Port {port}: returned status {response.status_code}")
            except Exception as e:
                print(f"Port {port}: {e}")
        
        print("❌ Host agent web interface is not accessible on ports 8000 or 8080")
        return False

async def run_integration_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("A2A Integration Test Suite")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    tests = [
        ("MCP Server", test_mcp_server),
        ("Marketo Agent", test_agent_card_retrieval),
        ("Host Agent", test_host_agent),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = await test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Your A2A integration should be working.")
        print("\nNext steps:")
        print("1. Open the host agent web interface: http://localhost:8000 or http://localhost:8080")
        print("2. Try the query: 'get me the campaign detail for id 4567'")
        print("3. The host agent should delegate to the Marketo agent successfully")
    else:
        print("❌ Some tests failed. Please check the services are running:")
        print("\nRequired services:")
        print("1. MCP Server (port 8002): python -m mcp-servers.marketo_server")
        print("2. Marketo Agent (port 10002): uv run --active .")
        print("3. Host Agent (port 8000/8080): uv run --active adk web")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
