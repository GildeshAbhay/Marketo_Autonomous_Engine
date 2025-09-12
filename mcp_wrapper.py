import asyncio
from fastmcp import Client

async def test_mcp():
    # Connect to your server (trailing slash optional; client handles it)
    client = Client("http://localhost:8002/mcp")
    async with client:
        # Step 1: Ping the server (basic connectivity)
        await client.ping()
        print("✅ Server ping successful!")

        # Step 2: List tools (should show get_campaign, trigger_campaign, update_smart_list)
        tools = await client.list_tools()
        print("Available tools:", tools)

        # Step 3: Call a read-only tool (replace 123 with a real campaign ID from Marketo)
        result = await client.call_tool("get_campaign", {"campaign_id": "6120"})
        print("get_campaign result:", result)

        # Optional: Test trigger_campaign (side-effecting; use real data cautiously)
        # payload = {"input": [{"id": your_lead_id}]}  # Uncomment with valid payload
        # trigger_result = await client.call_tool("trigger_campaign", {
        #     "campaign_id": 123,
        #     "input_payload": payload
        # })
        # print("trigger_campaign result:", trigger_result)

if __name__ == "__main__":
    asyncio.run(test_mcp())