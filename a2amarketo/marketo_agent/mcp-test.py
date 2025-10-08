import asyncio
from fastmcp import Client


async def test_mcp():
    # Connect to your server (trailing slash optional; client handles it)
    client = Client("http://localhost:8002/sse")
    async with client:
        # Step 1: Ping the server (basic connectivity)
        await client.ping()
        print("✅ Server ping successful!")

        # Step 2: List tools (should show get_campaign, trigger_campaign, update_smart_list)
        tools = await client.list_tools()
        print("Available tools:", tools)

        # Step 3: Call a read-only tool (replace 123 with a real campaign ID from Marketo)
        # result = await client.call_tool("get_leads_by_filter_type", {"filter_type": "email", "filter_values": ["Munnim@grazitti.com"], "fields": ["id", "email", "first_name", "last_name", "company"], "batch_size": 100})
        # print("get_campaign result:", result)

        # result = await client.call_tool("get_campaign", {"campaign_id": "10979"})
        # print("get_campaign result:", result)
        # result_2 = await client.call_tool("get_lead_by_id", {"lead_id": 6228, "fields": ["id", "email", "firstName", "lastName", "company"]})
        # print("get_lead_by_id result:", result_2)

        # result_1 = await client.call_tool("get_smart_list", {"smart_list_id": 26609})
        # print("get_campaign result:", result_1)

        result_1 = await client.call_tool("update_smart_campaign_by_id", {"smart_campaign_id": 10979 , "payload": {"description": "Test Description"}})
        print("smart campaign updated result:", result_1)
        # Optional: Test trigger_campaign (side-effecting; use real data cautiously)
        # payload = {"input": [{"id": your_lead_id}]}  # Uncomment with valid payload
        # trigger_result = await client.call_tool("trigger_campaign", {
        #     "campaign_id": 123,
        #     "input_payload": payload
        # })
        # print("trigger_campaign result:", trigger_result)

if __name__ == "__main__":
    asyncio.run(test_mcp())