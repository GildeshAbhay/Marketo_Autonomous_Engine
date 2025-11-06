"""
ActionAgent: encapsulates Marketo write/trigger operations. Keep actions idempotent and add safety checks.
"""
from typing import Any, Dict, Optional
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
    def get_tokens(self, folder_id: int, folder_type: str = "Folder") -> Dict[str, Any]:
        """Get My Tokens from a folder."""
        if not isinstance(folder_id, int):
            raise ValueError("folder_id must be an integer")
        if folder_type not in ["Folder", "Program"]:
            raise ValueError("folder_type must be 'Folder' or 'Program'")
        return self.client.get_tokens(folder_id, folder_type)

    # def update_program_tokens(self, program_id: int, tokens: Dict[str, str]) -> Dict[str, Any]:
    #     """Auto-populate My Tokens in a program."""
    #     if not isinstance(program_id, int):
    #         raise ValueError("program_id must be an integer")
    #     if not tokens or not isinstance(tokens, dict):
    #         raise ValueError("tokens must be a non-empty dictionary")
    #     return self.client.update_program_tokens(program_id, tokens)

    # Email Update Actions
    def get_email_by_name(
        self, 
        name: str, 
        status: str = None,
        folder: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get an email by name."""
        if not name or not isinstance(name, str):
            raise ValueError("name must be a non-empty string")
        if status and status not in ["approved", "draft"]:
            raise ValueError("status must be 'approved' or 'draft'")
        return self.client.get_email_by_name(name, status, folder)

    def get_email_by_id(self, email_id: int, status: str = None) -> Dict[str, Any]:
        """Get an email by ID."""
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        if status and status not in ["approved", "draft"]:
            raise ValueError("status must be 'approved' or 'draft'")
        return self.client.get_email_by_id(email_id, status)

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

    def update_email_content_fields(
        self, 
        email_id: int, 
        from_email: Dict[str, str] = None,
        from_name: Dict[str, str] = None,
        reply_to: Dict[str, str] = None,
        subject: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Update email header fields (fromEmail, fromName, replyTo, subject).
        
        Note: Email must be in draft/unapproved state to update these fields.
        The 'type' field should be 'Text' (capitalized).
        """
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        if not any([from_email, from_name, reply_to, subject]):
            raise ValueError("At least one header field must be provided")
        
        # Validate header field structure
        for field_name, field_value in [("from_email", from_email), ("from_name", from_name), 
                                         ("reply_to", reply_to), ("subject", subject)]:
            if field_value is not None:
                if not isinstance(field_value, dict):
                    raise ValueError(f"{field_name} must be a dictionary")
                if "type" not in field_value or "value" not in field_value:
                    raise ValueError(f"{field_name} must contain 'type' and 'value' keys")
                # Warn about proper case
                if field_value.get("type") and field_value["type"].lower() == "text" and field_value["type"] != "Text":
                    print(f"Warning: {field_name} type should be 'Text' (capitalized), auto-correcting from '{field_value['type']}'")
        
        return self.client.update_email_content_fields(email_id, from_email, from_name, reply_to, subject)

    def update_email_metadata(
        self, 
        email_id: int,
        description: str = None,
        name: str = None,
        pre_header: str = None,
        operational: bool = None,
        published: bool = None,
        text_only: bool = None,
        web_view: bool = None
    ) -> Dict[str, Any]:
        """Update email metadata."""
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        if not any([description is not None, name is not None, pre_header is not None,
                    operational is not None, published is not None, text_only is not None,
                    web_view is not None]):
            raise ValueError("At least one metadata field must be provided")
        
        return self.client.update_email_metadata(
            email_id, description, name, pre_header, 
            operational, published, text_only, web_view
        )

    def update_email_content_section(
        self, 
        email_id: int,
        html_id: str,
        content_type: str,
        value: str,
        alt_text: str = None,
        external_url: str = None,
        height: int = None,
        image: str = None,
        link_url: str = None,
        overwrite: bool = None,
        style: str = None,
        text_value: str = None,
        video_url: str = None,
        width: int = None
    ) -> Dict[str, Any]:
        """Update a specific email content section by htmlId."""
        if not isinstance(email_id, int):
            raise ValueError("email_id must be an integer")
        if not html_id or not isinstance(html_id, str):
            raise ValueError("html_id must be a non-empty string")
        if content_type not in ["Text", "DynamicContent", "Snippet"]:
            raise ValueError("content_type must be 'Text', 'DynamicContent', or 'Snippet'")
        if not value or not isinstance(value, str):
            raise ValueError("value must be a non-empty string")
        
        return self.client.update_email_content_section(
            email_id, html_id, content_type, value,
            alt_text, external_url, height, image, link_url,
            overwrite, style, text_value, video_url, width
        )

    def update_landing_page_content_section(
        self,
        landing_page_id: int,
        content_id: str,
        content_type: str,
        background_color: str = None,
        border_color: str = None,
        border_style: str = None,
        border_width: str = None,
        height: str = None,
        hide_desktop: bool = None,
        hide_mobile: bool = None,
        image_open_new_window: str = None,
        index: int = None,
        left: str = None,
        link_url: str = None,
        opacity: str = None,
        top: str = None,
        value: str = None,
        width: str = None,
        z_index: str = None
    ) -> Dict[str, Any]:
        """Update a specific landing page content section."""
        if not isinstance(landing_page_id, int):
            raise ValueError("landing_page_id must be an integer")
        if not content_id or not isinstance(content_id, str):
            raise ValueError("content_id must be a non-empty string")
        if content_type not in ["Image", "Form", "Rectangle", "Snippet", "RichText", "HTML", "DynamicContent"]:
            raise ValueError("content_type must be one of: Image, Form, Rectangle, Snippet, RichText, HTML, DynamicContent")
        
        return self.client.update_landing_page_content_section(
            landing_page_id, content_id, content_type,
            background_color, border_color, border_style, border_width,
            height, hide_desktop, hide_mobile, image_open_new_window,
            index, left, link_url, opacity, top, value, width, z_index
        )

    def update_landing_page_dynamic_content(
        self,
        landing_page_id: int,
        content_id: str,
        background_color: str = None,
        border_color: str = None,
        border_style: str = None,
        border_width: str = None,
        height: str = None,
        hide_desktop: bool = None,
        hide_mobile: bool = None,
        image_open_new_window: str = None,
        left: str = None,
        link_url: str = None,
        opacity: str = None,
        segment: str = None,
        top: str = None,
        content_type: str = None,
        value: str = None,
        width: str = None,
        z_index: str = None
    ) -> Dict[str, Any]:
        """Update a landing page dynamic content section."""
        if not isinstance(landing_page_id, int):
            raise ValueError("landing_page_id must be an integer")
        if not content_id or not isinstance(content_id, str):
            raise ValueError("content_id must be a non-empty string")
        
        return self.client.update_landing_page_dynamic_content(
            landing_page_id, content_id,
            background_color, border_color, border_style, border_width,
            height, hide_desktop, hide_mobile, image_open_new_window,
            left, link_url, opacity, segment, top, content_type,
            value, width, z_index
        )

    def add_landing_page_content_section(
        self,
        landing_page_id: int,
        content_id: str,
        content_type: str,
        background_color: str = None,
        border_color: str = None,
        border_style: str = None,
        border_width: str = None,
        height: str = None,
        hide_desktop: bool = None,
        hide_mobile: bool = None,
        image_open_new_window: str = None,
        left: str = None,
        link_url: str = None,
        opacity: str = None,
        top: str = None,
        value: str = None,
        width: str = None,
        z_index: str = None
    ) -> Dict[str, Any]:
        """Add a new content section to a landing page."""
        if not isinstance(landing_page_id, int):
            raise ValueError("landing_page_id must be an integer")
        if not content_id or not isinstance(content_id, str):
            raise ValueError("content_id must be a non-empty string")
        if content_type not in ["Image", "Form", "Rectangle", "Snippet", "RichText", "HTML"]:
            raise ValueError("content_type must be one of: Image, Form, Rectangle, Snippet, RichText, HTML")
        
        return self.client.add_landing_page_content_section(
            landing_page_id, content_id, content_type,
            background_color, border_color, border_style, border_width,
            height, hide_desktop, hide_mobile, image_open_new_window,
            left, link_url, opacity, top, value, width, z_index
        )

    def get_folder_program_contents(
        self,
        folder_id: int,
        folder_type: str = "Folder",
        max_return: int = None,
        offset: int = None
    ) -> Dict[str, Any]:
        """Get contents of a Marketo folder or program.
        
        Args:
            folder_id: ID of the folder to retrieve
            folder_type: Type of folder - 'Folder' or 'Program' (default: 'Folder')
            max_return: Maximum number of items to return (max 200, default 20)
            offset: Integer offset for paging
        
        Returns:
            Dictionary containing folder contents
        """
        if not isinstance(folder_id, int):
            raise ValueError("folder_id must be an integer")
        if folder_type not in ["Folder", "Program"]:
            raise ValueError("folder_type must be 'Folder' or 'Program'")
        if max_return is not None:
            if not isinstance(max_return, int):
                raise ValueError("max_return must be an integer")
            if max_return > 200:
                raise ValueError("max_return cannot exceed 200")
        if offset is not None and not isinstance(offset, int):
            raise ValueError("offset must be an integer")
        
        return self.client.get_folder_program_contents(folder_id, folder_type, max_return, offset)

    def bulk_import_leads(self, file_path: str, format: str = "csv", lookup_field: str = "email", partition_name: str = None, list_id: int = None) -> Dict[str, Any]:
        """Import leads from a file into Marketo."""
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path must be a non-empty string")
        if format not in ["csv", "tsv", "ssv"]:
            raise ValueError("format must be one of: csv, tsv, ssv")
        return self.client.bulk_import_leads(file_path, format, lookup_field, partition_name, list_id)