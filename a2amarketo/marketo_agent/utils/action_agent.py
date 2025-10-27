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
    
    def create_smart_campaign(self, name: str, folder_id: int, folder_type: str, description: str = "") -> Dict[str, Any]:
        """Create a new smart campaign in Marketo."""
        if not name or not isinstance(name, str):
            raise ValueError("name must be a non-empty string")
        if not isinstance(folder_id, int):
            raise ValueError("folder_id must be an integer")
        if folder_type not in ["Folder", "Program"]:
            raise ValueError("folder_type must be 'Folder' or 'Program'")
        
        return self.client.create_smart_campaign(name, folder_id, folder_type, description)
    
    def update_smart_campaign(self, smart_campaign_id: int, name: str = None, description: str = None) -> Dict[str, Any]:
        """Update a smart campaign's name and/or description."""
        if not isinstance(smart_campaign_id, int):
            raise ValueError("smart_campaign_id must be an integer")
        if name is None and description is None:
            raise ValueError("At least one of 'name' or 'description' must be provided")
        
        return self.client.update_smart_campaign(smart_campaign_id, name, description)

    def trigger_campaign(self, campaign_id: int, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a campaign with a payload. Validate payload before calling Marketo."""
        # Basic validation example
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be int")
        return self.client.trigger_campaign(campaign_id, input_payload)

    def get_smart_list(self, smart_list_id: int) -> Dict[str, Any]:
        return self.client.get_smart_list(smart_list_id)

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

    def get_program_by_id(self, program_id: int) -> Dict[str, Any]:
        """Fetch a program by ID."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        return self.client.get_program_by_id(program_id)

    def get_program_by_name(
        self, 
        name: str, 
        include_tags: bool = False,
        include_costs: bool = False
    ) -> Dict[str, Any]:
        """Fetch a program by name with optional tags and costs."""
        if not name or not isinstance(name, str):
            raise ValueError("name must be a non-empty string")
        return self.client.get_program_by_name(name, include_tags, include_costs)

    def clone_program(
        self, 
        program_id: int, 
        name: str,
        folder_id: int,
        folder_type: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """Clone an existing program."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        if not name or not isinstance(name, str):
            raise ValueError("name must be a non-empty string")
        if len(name) > 255:
            raise ValueError("name must not exceed 255 characters")
        if not isinstance(folder_id, int):
            raise ValueError("folder_id must be an integer")
        if folder_type not in ["Folder", "Program"]:
            raise ValueError("folder_type must be 'Folder' or 'Program'")
        
        return self.client.clone_program(program_id, name, folder_id, folder_type, description)

    # Token Update Actions
    def get_program_tokens(self, program_id: int) -> Dict[str, Any]:
        """Get My Tokens from a program."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        return self.client.get_program_tokens(program_id)

    def update_program_tokens(self, program_id: int, tokens: Dict[str, str]) -> Dict[str, Any]:
        """Auto-populate My Tokens in a program."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        if not tokens or not isinstance(tokens, dict):
            raise ValueError("tokens must be a non-empty dictionary")
        return self.client.update_program_tokens(program_id, tokens)

    # Email Update Actions
    def get_program_emails(self, program_id: int) -> Dict[str, Any]:
        """Get all email assets from a program."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        return self.client.get_program_emails(program_id)

    def get_email_content(self, email_id: int) -> Dict[str, Any]:
        """Get email content including subject line and body."""
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        return self.client.get_email_content(email_id)

    def update_email_content(self, email_id: int, content_updates: Dict[str, str]) -> Dict[str, Any]:
        """Update email content variables."""
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        if not content_updates or not isinstance(content_updates, dict):
            raise ValueError("content_updates must be a non-empty dictionary")
        return self.client.update_email_content(email_id, content_updates)

    def approve_email(self, email_id: int) -> Dict[str, Any]:
        """Approve an email asset."""
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        return self.client.approve_email(email_id)

    # Landing Page Update Actions
    def get_program_landing_pages(self, program_id: int) -> Dict[str, Any]:
        """Get all landing page assets from a program."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        return self.client.get_program_landing_pages(program_id)

    def get_landing_page_content(self, landing_page_id: int) -> Dict[str, Any]:
        """Get landing page content sections."""
        if not isinstance(landing_page_id, int):
            raise ValueError("landing_page_id must be an integer")
        return self.client.get_landing_page_content(landing_page_id)

    def update_landing_page_content(self, landing_page_id: int, content_updates: Dict[str, str]) -> Dict[str, Any]:
        """Update landing page editable sections."""
        if not isinstance(landing_page_id, int):
            raise ValueError("landing_page_id must be an integer")
        if not content_updates or not isinstance(content_updates, dict):
            raise ValueError("content_updates must be a non-empty dictionary")
        return self.client.update_landing_page_content(landing_page_id, content_updates)

    def approve_landing_page(self, landing_page_id: int) -> Dict[str, Any]:
        """Approve a landing page asset."""
        if not isinstance(landing_page_id, int):
            raise ValueError("landing_page_id must be an integer")
        return self.client.approve_landing_page(landing_page_id)

    # Smart List Actions
    def get_smart_list_rules(self, smart_list_id: int) -> Dict[str, Any]:
        """Get smart list filter rules."""
        if not isinstance(smart_list_id, int):
            raise ValueError("smart_list_id must be an integer")
        return self.client.get_smart_list_rules(smart_list_id)

    def update_smart_list_rules(self, smart_list_id: int, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart list filter criteria."""
        if not isinstance(smart_list_id, int):
            raise ValueError("smart_list_id must be an integer")
        if not rules or not isinstance(rules, dict):
            raise ValueError("rules must be a non-empty dictionary")
        return self.client.update_smart_list_rules(smart_list_id, rules)

    # Smart Campaign Actions
    def get_smart_campaign_rules(self, campaign_id: int) -> Dict[str, Any]:
        """Get smart campaign smart list rules."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        return self.client.get_smart_campaign_rules(campaign_id)

    def update_smart_campaign_rules(self, campaign_id: int, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart campaign filter criteria."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        if not rules or not isinstance(rules, dict):
            raise ValueError("rules must be a non-empty dictionary")
        return self.client.update_smart_campaign_rules(campaign_id, rules)

    def get_smart_campaign_flow(self, campaign_id: int) -> Dict[str, Any]:
        """Get smart campaign flow steps."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        return self.client.get_smart_campaign_flow(campaign_id)

    def update_smart_campaign_flow(self, campaign_id: int, flow_steps: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart campaign flow."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        if not flow_steps or not isinstance(flow_steps, dict):
            raise ValueError("flow_steps must be a non-empty dictionary")
        return self.client.update_smart_campaign_flow(campaign_id, flow_steps)

    def activate_smart_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Activate a smart campaign."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        return self.client.activate_smart_campaign(campaign_id)

    def schedule_smart_campaign(self, campaign_id: int, run_at: str, recipients: Dict[str, Any] = None) -> Dict[str, Any]:
        """Schedule a smart campaign."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        if not run_at or not isinstance(run_at, str):
            raise ValueError("run_at must be a non-empty string")
        return self.client.schedule_smart_campaign(campaign_id, run_at, recipients)

    # Token Update Actions
    def get_program_tokens(self, program_id: int) -> Dict[str, Any]:
        """Get My Tokens from a program."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        return self.client.get_program_tokens(program_id)

    def update_program_tokens(self, program_id: int, tokens: Dict[str, str]) -> Dict[str, Any]:
        """Auto-populate My Tokens in a program."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        if not tokens or not isinstance(tokens, dict):
            raise ValueError("tokens must be a non-empty dictionary")
        return self.client.update_program_tokens(program_id, tokens)

    # Email Update Actions
    def get_program_emails(self, program_id: int) -> Dict[str, Any]:
        """Get all email assets from a program."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        return self.client.get_program_emails(program_id)

    def get_email_content(self, email_id: int) -> Dict[str, Any]:
        """Get email content including subject line and body."""
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        return self.client.get_email_content(email_id)

    def update_email_content(self, email_id: int, content_updates: Dict[str, str]) -> Dict[str, Any]:
        """Update email content variables."""
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        if not content_updates or not isinstance(content_updates, dict):
            raise ValueError("content_updates must be a non-empty dictionary")
        return self.client.update_email_content(email_id, content_updates)

    def approve_email(self, email_id: int) -> Dict[str, Any]:
        """Approve an email asset."""
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        return self.client.approve_email(email_id)

    # Landing Page Update Actions
    def get_program_landing_pages(self, program_id: int) -> Dict[str, Any]:
        """Get all landing page assets from a program."""
        if not isinstance(program_id, int):
            raise ValueError("program_id must be an integer")
        return self.client.get_program_landing_pages(program_id)

    def get_landing_page_content(self, landing_page_id: int) -> Dict[str, Any]:
        """Get landing page content sections."""
        if not isinstance(landing_page_id, int):
            raise ValueError("landing_page_id must be an integer")
        return self.client.get_landing_page_content(landing_page_id)

    def update_landing_page_content(self, landing_page_id: int, content_updates: Dict[str, str]) -> Dict[str, Any]:
        """Update landing page editable sections."""
        if not isinstance(landing_page_id, int):
            raise ValueError("landing_page_id must be an integer")
        if not content_updates or not isinstance(content_updates, dict):
            raise ValueError("content_updates must be a non-empty dictionary")
        return self.client.update_landing_page_content(landing_page_id, content_updates)

    def approve_landing_page(self, landing_page_id: int) -> Dict[str, Any]:
        """Approve a landing page asset."""
        if not isinstance(landing_page_id, int):
            raise ValueError("landing_page_id must be an integer")
        return self.client.approve_landing_page(landing_page_id)

    # Smart List Actions
    def get_smart_list_rules(self, smart_list_id: int) -> Dict[str, Any]:
        """Get smart list filter rules."""
        if not isinstance(smart_list_id, int):
            raise ValueError("smart_list_id must be an integer")
        return self.client.get_smart_list_rules(smart_list_id)

    def update_smart_list_rules(self, smart_list_id: int, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart list filter criteria."""
        if not isinstance(smart_list_id, int):
            raise ValueError("smart_list_id must be an integer")
        if not rules or not isinstance(rules, dict):
            raise ValueError("rules must be a non-empty dictionary")
        return self.client.update_smart_list_rules(smart_list_id, rules)

    # Smart Campaign Actions
    def get_smart_campaign_rules(self, campaign_id: int) -> Dict[str, Any]:
        """Get smart campaign smart list rules."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        return self.client.get_smart_campaign_rules(campaign_id)

    def update_smart_campaign_rules(self, campaign_id: int, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart campaign filter criteria."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        if not rules or not isinstance(rules, dict):
            raise ValueError("rules must be a non-empty dictionary")
        return self.client.update_smart_campaign_rules(campaign_id, rules)

    def get_smart_campaign_flow(self, campaign_id: int) -> Dict[str, Any]:
        """Get smart campaign flow steps."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        return self.client.get_smart_campaign_flow(campaign_id)

    def update_smart_campaign_flow(self, campaign_id: int, flow_steps: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart campaign flow."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        if not flow_steps or not isinstance(flow_steps, dict):
            raise ValueError("flow_steps must be a non-empty dictionary")
        return self.client.update_smart_campaign_flow(campaign_id, flow_steps)

    def activate_smart_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Activate a smart campaign."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        return self.client.activate_smart_campaign(campaign_id)

    def schedule_smart_campaign(self, campaign_id: int, run_at: str, recipients: Dict[str, Any] = None) -> Dict[str, Any]:
        """Schedule a smart campaign."""
        if not isinstance(campaign_id, int):
            raise ValueError("campaign_id must be an integer")
        if not run_at or not isinstance(run_at, str):
            raise ValueError("run_at must be a non-empty string")
        return self.client.schedule_smart_campaign(campaign_id, run_at, recipients)


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