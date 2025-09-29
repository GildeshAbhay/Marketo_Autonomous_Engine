"""
ActionAgent: encapsulates Marketo write/trigger operations. Keep actions idempotent and add safety checks.
"""
from typing import Any, Dict
from .marketo_client import MarketoClient

try:
    from google.adk import Agent as ADKAgent # type: ignore
    ADK_AVAILABLE = True
except Exception:
    ADK_AVAILABLE = False


class ActionAgent:
    def __init__(self, marketo_client: MarketoClient):
        self.client = marketo_client

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        return self.client.get_campaign(campaign_id)

    def trigger_campaign(self, campaign_id: int, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a campaign with a payload. Validate payload before calling Marketo."""
        # Basic validation example
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be int")
            return self.client.trigger_campaign(campaign_id, input_payload)

    def update_smart_list(self, smart_list_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.update_smart_list(smart_list_id, payload)

if ADK_AVAILABLE:
    print("ADK is available")
    def make_adk_action_agent(marketo_client: MarketoClient) -> ADKAgent:
        action_agent = ActionAgent(marketo_client)
        adk_agent = ADKAgent(model="gpt-4o-mini", name="marketo-action-agent", instruction="Execute Marketo actions safely, use DataAgent for reads if needed")
        #adk_agent = ADKAgent(model="gpt-4o-mini", name="marketo-action-agent", instruction="Execute Marketo actions safely")
        # Add tools
        adk_agent.add_tool(action_agent.trigger_campaign)
        adk_agent.add_tool(action_agent.update_smart_list)
        # A2A: Add DataAgent as a sub-agent/tool
        data_adk = make_adk_data_agent(marketo_client)  # From data_agent.py
        adk_agent.add_sub_agent(data_adk)  # Or adk_agent.tools.register(data_adk.get_campaign_details)
        # wire up tools in ADK as needed
        return adk_agent