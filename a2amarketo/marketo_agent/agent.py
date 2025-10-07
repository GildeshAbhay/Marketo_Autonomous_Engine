import os
from typing import Dict, List, Any
import json
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
from google.adk.agents import LlmAgent
from utils.marketo_client import MarketoClient

# # Initialize Marketo client
# def get_marketo_client() -> MarketoClient:
#     """Initialize Marketo client from environment variables."""
#     client_id = os.getenv("MARKETO_CLIENT_ID")
#     client_secret = os.getenv("MARKETO_CLIENT_SECRET")
#     identity_base = os.getenv("MARKETO_IDENTITY_BASE")
#     rest_base = os.getenv("MARKETO_REST_BASE")
    
#     if not all([client_id, client_secret, identity_base, rest_base]):
#         raise ValueError("Missing required Marketo environment variables: MARKETO_CLIENT_ID, MARKETO_CLIENT_SECRET, MARKETO_IDENTITY_BASE, MARKETO_REST_BASE")
    
#     return MarketoClient(client_id, client_secret, identity_base, rest_base)


# def get_marketo_campaigns() -> str:
#     """
#     Retrieves information about Marketo campaigns.
    
#     Returns:
#         A string containing campaign information.
#     """
#     try:
#         client = get_marketo_client()
#         response = client.get_campaigns()
        
#         if not response.get("result"):
#             return "No campaigns found in Marketo."
        
#         campaigns = response["result"]
#         result = "Available Marketo Campaigns:\n"
#         for campaign in campaigns:
#             result += f"• {campaign.get('name', 'Unknown')} (ID: {campaign.get('id', 'Unknown')}) - Status: {campaign.get('status', 'Unknown')}\n"
        
#         return result
#     except Exception as e:
#         return f"Error retrieving campaigns: {str(e)}"


# def get_marketo_smart_lists() -> str:
#     """
#     Retrieves information about Marketo smart lists.
    
#     Returns:
#         A string containing smart list information.
#     """
#     try:
#         client = get_marketo_client()
#         response = client.get_smart_lists()
        
#         if not response.get("result"):
#             return "No smart lists found in Marketo."
        
#         smart_lists = response["result"]
#         result = "Available Marketo Smart Lists:\n"
#         for sl in smart_lists:
#             result += f"• {sl.get('name', 'Unknown')} (ID: {sl.get('id', 'Unknown')}) - Description: {sl.get('description', 'No description')}\n"
        
#         return result
#     except Exception as e:
#         return f"Error retrieving smart lists: {str(e)}"


# def get_marketo_leads(filter_type: str = "email", filter_values: str = "") -> str:
#     """
#     Retrieves information about Marketo leads.
    
#     Args:
#         filter_type: Type of filter to apply (email, id, etc.).
#         filter_values: Comma-separated values to filter by.
    
#     Returns:
#         A string containing lead information.
#     """
#     try:
#         client = get_marketo_client()
        
#         # Parse filter values
#         filter_list = [v.strip() for v in filter_values.split(",") if v.strip()] if filter_values else []
        
#         if filter_list:
#             response = client.get_leads(filter_type=filter_type, filter_values=filter_list)
#         else:
#             # Get all leads (this might be limited by Marketo API)
#             response = client.get_leads()
        
#         if not response.get("result"):
#             return "No leads found in Marketo."
        
#         leads = response["result"]
#         result = f"Marketo Leads (filter: {filter_type}={filter_values}):\n"
#         for lead in leads:
#             result += f"• {lead.get('email', 'No email')} - ID: {lead.get('id', 'Unknown')} - Company: {lead.get('company', 'Unknown')}\n"
        
#         return result
#     except Exception as e:
#         return f"Error retrieving leads: {str(e)}"


# def create_marketo_smart_list(name: str, description: str, folder_id: int = 1) -> str:
#     """
#     Creates a new smart list in Marketo.
    
#     Args:
#         name: Name of the smart list.
#         description: Description of the smart list.
#         folder_id: ID of the folder to create the smart list in (default: 1).
    
#     Returns:
#         A string confirming the smart list creation.
#     """
#     try:
#         client = get_marketo_client()
#         response = client.create_smart_list(name, description, folder_id)
        
#         if response.get("result"):
#             smart_list = response["result"][0]  # Marketo returns array
#             return f"Successfully created smart list '{name}' with ID {smart_list.get('id', 'Unknown')}. Description: {description}"
#         else:
#             return f"Failed to create smart list: {response.get('errors', 'Unknown error')}"
        
#     except Exception as e:
#         return f"Error creating smart list: {str(e)}"


def create_agent() -> LlmAgent:
    """Constructs the ADK agent for Marketo operations."""
    return LlmAgent(
        model="gemini-2.5-flash",
        name="Marketo_Campaign_Agent",
        instruction="""
            **Role:** You are a Marketo operations assistant. 
            Your primary responsibility is to help users manage their Marketo instance 
            by providing information about campaigns, smart lists, leads, and other assets.

            
        """,
        tools=[MCPToolset(
            connection_params=SseServerParams(
                url="http://localhost:8002/sse",  # Connect to your FastMCP server via HTTP/SSE
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

