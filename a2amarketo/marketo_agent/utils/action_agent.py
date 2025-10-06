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

    def get_lead_by_id(self, lead_id: int, fields: list[str] = None) -> Dict[str, Any]:
        """Fetch a lead by ID with optional field filtering."""
        return self.client.get_lead_by_id(lead_id, fields)

    def get_leads_by_filter_type(self, filter_type: str, filter_values: list[str], fields: list[str] = None, batch_size: int = 300) -> Dict[str, Any]:
        """Fetch multiple leads by filter type (email, id, etc.)."""
        return self.client.get_leads_by_filter_type(filter_type, filter_values, fields, batch_size)

    def describe_lead(self) -> Dict[str, Any]:
        """Get metadata about available lead fields."""
        return self.client.describe_lead()

    def get_lead_partitions(self) -> Dict[str, Any]:
        """Get all lead partitions."""
        return self.client.get_lead_partitions()

    def get_leads_by_program(self, program_id: int, fields: list[str] = None, batch_size: int = 300) -> Dict[str, Any]:
        """Get leads that are members of a specific program."""
        return self.client.get_leads_by_program(program_id, fields, batch_size)

    def get_leads_by_smart_list(self, smart_list_id: int, fields: list[str] = None, batch_size: int = 300, next_page_token: str = None) -> Dict[str, Any]:
        """Get leads that are members of a specific Smart List."""
        return self.client.get_leads_by_smart_list(smart_list_id, fields, batch_size, next_page_token)


# if ADK_AVAILABLE:
#     print("ADK is available")
#     def make_adk_action_agent(marketo_client: MarketoClient) -> ADKAgent:
#         action_agent = ActionAgent(marketo_client)
#         adk_agent = ADKAgent(model="gpt-4o-mini", name="marketo-action-agent", instruction="Execute Marketo actions safely, use DataAgent for reads if needed")
#         #adk_agent = ADKAgent(model="gpt-4o-mini", name="marketo-action-agent", instruction="Execute Marketo actions safely")
#         # Add tools
#         adk_agent.add_tool(action_agent.trigger_campaign)
#         adk_agent.add_tool(action_agent.update_smart_list)
#         # A2A: Add DataAgent as a sub-agent/tool
#         data_adk = make_adk_data_agent(marketo_client)  # From data_agent.py
#         adk_agent.add_sub_agent(data_adk)  # Or adk_agent.tools.register(data_adk.get_campaign_details)
#         # wire up tools in ADK as needed
#         return adk_agent