from fastmcp import Client

client = Client("http://127.0.0.1:8001")  # HTTP MCP server URL

import asyncio

async def test():
    async with client:  # preferred usage context
        tools = await client.list_tools()
        print("Available tools:", tools)

        # Call a specific tool (e.g. get_campaign_details)
        response = await client.call_tool("get_campaign_details", {"campaign_id": 123})
        print("Response:", response)

asyncio.run(test())
