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

        # result_1 = await client.call_tool("update_smart_campaign_by_id", {"smart_campaign_id": 10979 , "name": "Change_name_testing_1"})
        # print("smart campaign updated result:", result_1)

        # result_1 = await client.call_tool("create_smart_campaign", {"name": "creating_smart_campaign_mcp", "folder_id": 9245, "folder_type": "Folder", "description": "Create_smart_campaign_description_testing_1"})
        # print("smart campaign created result:", result_1)

        # result_2 = await client.call_tool("clone_program", {"program_id": 4713, "name": "Cloned_program_mcp_2", "folder_id": 9245, "folder_type": "Folder", "description": "Clone_program_description_testing_1"})
        # print("Cloned program id:", result_2)
        
        # Optional: Test trigger_campaign (side-effecting; use real data cautiously)
        # payload = {"input": [{"id": your_lead_id}]}  # Uncomment with valid payload
        # trigger_result = await client.call_tool("trigger_campaign", {
        #     "campaign_id": 123,
        #     "input_payload": payload
        # })
        # print("trigger_campaign result:", trigger_result)
        # result = await client.call_tool("update_program_tokens", {
        # "program_id": 4713,
        # "tokens": {
        #     "my.text.token": "Hello, this is an automated update!",
        #     "my.url.token": "https://example.com/thankyou"
        #     }})

        # result= await client.call_tool("update_email_content_fields", {
        #     "email_id": 12139,
        #     "from_email": {
        #         "type": "Text",
        #         "value": "saksham_dubey@grazitti.com"
        #     }})

        # print("Updated program tokens result:", result)

        fields_result = await client.call_tool("describe_lead", {})
        print("Lead fields:", fields_result)
        
        # Test bulk import leads with minimal fields
        result = await client.call_tool("bulk_import_leads", {
            "file_path": r"C:\Users\sanchita.jain\Downloads\marketo a2a\Marketo_Autonomous_Engine\a2amarketo\marketo_leads_sample_minimal.csv",
            "format": "csv",
            "lookup_field": "email"
        })
        print("Bulk import leads result:", result)


if __name__ == "__main__":
    asyncio.run(test_mcp())