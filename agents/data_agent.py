"""
DataAgent: encapsulates Marketo read-only operations. This agent exposes simple methods
that can be called directly or wrapped by ADK/ MCP.
"""
from typing import Any, Dict
from marketo_client import MarketoClient
try:
    # optional: show how ADK could be used if installed
    from google.adk import Agent as ADKAgent # type: ignore
    ADK_AVAILABLE = True
except Exception:
    ADK_AVAILABLE = False


class DataAgent:
    def __init__(self, marketo_client: MarketoClient):
        self.client = marketo_client

    def get_campaign_details(self, campaign_id: int) -> Dict[str, Any]:
        """Return campaign asset details in a normalized dict."""
        return self.client.get_campaign(campaign_id)

    def get_smart_list(self, smart_list_id: int) -> Dict[str, Any]:
        return self.client.get_smart_list(smart_list_id)

    def get_campaign_members(self, campaign_id: int, offset: int = 0) -> Dict[str, Any]:
        return self.client.get_campaign_members(campaign_id, offset)


# Optionally expose ADK agent wrapper (POC)
if ADK_AVAILABLE:
    # This is illustrative — an ADK Agent would be configured with tools that call the methods above
    def make_adk_data_agent(marketo_client: MarketoClient) -> ADKAgent:
        """Return a minimal ADK Agent that wraps DataAgent. Fill in model and prompts as needed."""
        data_agent = DataAgent(marketo_client)
        # The exact ADK APIs are richer — this is a placeholder showing how you'd embed tools.
        adk_agent = ADKAgent(model="gpt-4o-mini", name="marketo-data-agent", instruction="Handle Marketo GET requests")
        # additional ADK tool wiring would go here
        return adk_agent
