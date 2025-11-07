import os
from typing import Dict, List, Any
import json
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
from google.adk.agents import LlmAgent
from .utils.marketo_client import MarketoClient
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.config_loader import get_config

deployment_config = get_config()

def create_agent() -> LlmAgent:
    """Constructs the ADK agent for Marketo operations."""
    return LlmAgent(
        model="gemini-2.5-flash",
        name="Marketo_Campaign_Agent",
        instruction="""
            **Role:** You are a Marketo operations assistant. 
            Your primary responsibility is to help users manage their Marketo instance 
            by providing information about campaigns, smart lists, leads, and other assets.

            **File Upload Support:**
            When a user query includes [FILE_PATH: /path/to/file.csv], extract the file path
            and use it with the bulk_import_leads tool. The file path is already saved on 
            the server and ready to be used.
            
            **Example:**
            User: "Import leads from the attached CSV file"
            Query includes: [FILE_PATH: /uploaded_files/user_20250107_143022_leads.csv]
            Action: Call bulk_import_leads with file_path="/uploaded_files/user_20250107_143022_leads.csv"
        """,
        tools=[MCPToolset(
                connection_params=SseServerParams(
                url=deployment_config.get_service_url("mcp_server") + "/sse",
                )
                )],
    )


# **Core Directives:**

# *   **Campaign Management:** Use the get_campaign tool to retrieve information about specific campaigns by ID.
# *   **Smart List Operations:** Use the available tools to view existing smart lists and create or update them as needed.
# *   **Lead Management:** Use the available tools to search and filter leads based on various criteria.
# *   **Tool Usage:** Always use the appropriate MCP tools to fetch real data from Marketo. Available tools include:
#     - get_campaign(campaign_id): Get details for a specific campaign
#     - trigger_campaign(campaign_id, input_payload): Trigger a campaign
#     - update_smart_list(smart_list_id, payload): Update a smart list
# *   **Response Format:** Provide clear, structured responses with the actual data from Marketo.
# *   **Error Handling:** If tools return errors, explain the issue clearly and suggest alternatives.
# *   **Data Accuracy:** Always use tools to get current data; never make up information.

