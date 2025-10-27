import time
import requests
from typing import Any, Dict, Optional
import json

class MarketoClient:
    """Simple Marketo REST wrapper with token caching.
    Configure with:
    client_id, client_secret, identity_base (no trailing slash), rest_base
    """
    def __init__(self, client_id: str, client_secret: str, identity_base: str, rest_base: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.identity_base = identity_base.rstrip("/")
        self.rest_base = rest_base.rstrip("/")
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0
        print("rest_base is", self.rest_base)


    def _ensure_token(self) -> str:
        now = time.time()
        if self._access_token and now < (self._token_expiry - 30):
            return self._access_token

        token_url = f"{self.identity_base}/oauth/token"
        print("identity_base is", self.identity_base)
        params = {
        "grant_type": "client_credentials",
        "client_id": self.client_id,
        "client_secret": self.client_secret,
        }
        resp = requests.get(token_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        self._token_expiry = now + int(expires_in)
        return self._access_token


    def _request(self, method: str, path: str, params: Dict[str, Any] | None = None, json: Dict[str, Any] | None = None) -> Dict[str, Any]:
        token = self._ensure_token()
        print(f"Token: {token}")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"{self.rest_base}{path}"
        print(f"URL to hit: {url} , and payload: {json}")
        resp = requests.request(method, url, params=params, json=json, headers=headers, timeout=15)
        resp.raise_for_status()
        print(f"Response: {resp.json()}")
        # Marketo responses usually wrap results in a 'result' field; return raw json for now
        return resp.json()

    def _request_form(self, method: str, path: str, params: Dict[str, Any] | None = None, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Request method for form-encoded data (application/x-www-form-urlencoded)"""
        token = self._ensure_token()
        print(f"Token: {token}")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/x-www-form-urlencoded"}
        url = f"{self.rest_base}{path}"
        print(f"URL to hit: {url} , and payload: {data}")
        resp = requests.request(method, url, params=params, data=data, headers=headers, timeout=15)
        resp.raise_for_status()
        print(f"Response: {resp.json()}")
        return resp.json()


    # -- Example helper methods (adjust endpoints for the fields you need) --
    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Fetch campaign asset details.
        Endpoint pattern: GET /rest/asset/v1/smartCampaign/{id}.json
        """
        path = f"/rest/asset/v1/smartCampaign/{campaign_id}.json"
        return self._request("GET", path)


    def get_smart_list(self, smart_list_id: int) -> Dict[str, Any]:
        """Fetch a smart list asset.
        Endpoint pattern: GET /rest/asset/v1/smart/list/{id}.json
        """
        path = f"/rest/asset/v1/smartList/{smart_list_id}.json"
        return self._request("GET", path)


    def get_campaign_members(self, campaign_id: int, offset: int = 0, max_return: int = 200) -> Dict[str, Any]:
        """Example: list members for a campaign (if applicable) - adapt as needed.
        This is illustrative; you may need different endpoints for campaign results or lead lists.
        """
        # Marketo endpoints vary; adapt to the exact API you need.
        path = f"/rest/v1/campaigns/{campaign_id}/members.json"
        params = {"offset": offset, "maxReturn": max_return}
        return self._request("GET", path, params=params)

    def create_smart_campaign(self, name: str, folder_id: int, folder_type: str, description: str = "") -> Dict[str, Any]:
        """Create a new smart campaign.
        Endpoint: POST /rest/asset/v1/smartCampaigns.json
        
        Args:
            name: Name of the smart campaign
            folder_id: ID of the folder to create the campaign in
            folder_type: Type of folder (e.g., 'Folder' or 'Program')
            description: Optional description of the campaign
        
        Returns:
            API response with created campaign details
        """
        path = "/rest/asset/v1/smartCampaigns.json"
        data = {
            "name": name,
            "folder": json.dumps({"id": folder_id, "type": folder_type}),
            "description": description
        }
        return self._request_form("POST", path, data=data)

    def update_smart_campaign(self, smart_campaign_id: int, name: str = None, description: str = None) -> Dict[str, Any]:
        """Update a smart campaign's name and/or description.
        Endpoint: POST /rest/asset/v1/smartCampaign/{id}.json
        
        Args:
            smart_campaign_id: The ID of the smart campaign to update
            name: Optional new name for the campaign
            description: Optional new description for the campaign
        
        Returns:
            API response with updated campaign details
        """
        path = f"/rest/asset/v1/smartCampaign/{smart_campaign_id}.json"
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        
        if not data:
            raise ValueError("At least one of 'name' or 'description' must be provided")
        
        return self._request_form("POST", path, data=data)

    def trigger_campaign(self, campaign_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a campaign. Example endpoint: POST /rest/v1/campaigns/{id}/trigger.json
        payload should follow Marketo trigger payloads (e.g., {'input': [{'id': leadId}]})
        """
        path = f"/rest/v1/campaigns/{campaign_id}/trigger.json"
        return self._request("POST", path, json=payload)



    def get_lead_by_id(self, lead_id: int, fields: Optional[list[str]] = None) -> Dict[str, Any]:
        """Fetch a lead by ID.
        Endpoint: GET /rest/v1/lead/{id}.json
        
        Args:
            lead_id: The Marketo lead ID
            fields: Optional list of field names to return. If None, returns all fields.
        
        Returns:
            Lead details dictionary
        """
        path = f"/rest/v1/lead/{lead_id}.json"
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        return self._request("GET", path, params=params if params else None)

    def get_leads_by_filter_type(
        self, 
        filter_type: str, 
        filter_values: list[str], 
        fields: Optional[list[str]] = None,
        batch_size: int = 300
    ) -> Dict[str, Any]:
        """Fetch multiple leads by filter type (email, id, cookie, etc.).
        Endpoint: GET /rest/v1/leads.json
        
        Args:
            filter_type: Type of filter (e.g., 'email', 'id', 'cookie')
            filter_values: List of values to filter by
            fields: Optional list of field names to return
            batch_size: Number of leads to return (max 300)
        
        Returns:
            Dictionary containing list of leads
        """
        path = "/rest/v1/leads.json"
        params = {
            "filterType": filter_type,
            "filterValues": ",".join(str(v) for v in filter_values),
            "batchSize": min(batch_size, 300)
        }
        if fields:
            params["fields"] = ",".join(fields)
        return self._request("GET", path, params=params)

    def describe_lead(self) -> Dict[str, Any]:
        """Get metadata about available lead fields.
        Endpoint: GET /rest/v1/leads/describe.json
        
        Returns:
            Dictionary containing field metadata (field names, types, etc.)
        """
        path = "/rest/v1/leads/describe.json"
        return self._request("GET", path)

    def get_lead_partitions(self) -> Dict[str, Any]:
        """Get all lead partitions in the Marketo instance.
        Endpoint: GET /rest/v1/leads/partitions.json
        
        Returns:
            Dictionary containing list of lead partitions
        """
        path = "/rest/v1/leads/partitions.json"
        return self._request("GET", path)

    def get_leads_by_program(
        self, 
        program_id: int, 
        fields: Optional[list[str]] = None,
        batch_size: int = 300
    ) -> Dict[str, Any]:
        """Get leads that are members of a specific program.
        Endpoint: GET /rest/v1/leads/programs/{programId}.json
        
        Args:
            program_id: The Marketo program ID
            fields: Optional list of field names to return
            batch_size: Number of leads to return (max 300)
        
        Returns:
            Dictionary containing list of leads in the program
        """
        path = f"/rest/v1/leads/programs/{program_id}.json"
        params = {"batchSize": min(batch_size, 300)}
        if fields:
            params["fields"] = ",".join(fields)
        return self._request("GET", path, params=params)

    def get_leads_by_smart_list(
        self, 
        smart_list_id: int, 
        fields: Optional[list[str]] = None,
        batch_size: int = 300,
        next_page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get leads that are members of a specific Smart List.
        Endpoint: GET /rest/v1/smartList/{smartListId}/leads.json
        
        Args:
            smart_list_id: The Marketo Smart List ID
            fields: Optional list of field names to return
            batch_size: Number of leads to return (max 300)
            next_page_token: Token for pagination
        
        Returns:
            Dictionary containing list of leads and pagination info
        """
        path = f"/rest/v1/smartList/{smart_list_id}/leads.json"
        params = {"batchSize": min(batch_size, 300)}
        if fields:
            params["fields"] = ",".join(fields)
        if next_page_token:
            params["nextPageToken"] = next_page_token
        return self._request("GET", path, params=params)

    def get_program_by_id(self, program_id: int) -> Dict[str, Any]:
        """Get a program by its ID.
        Endpoint: GET /rest/asset/v1/program/{id}.json
        
        Args:
            program_id: The Marketo program ID
        
        Returns:
            Dictionary containing program details
        """
        path = f"/rest/asset/v1/program/{program_id}.json"
        return self._request("GET", path)

    def get_program_by_name(
        self, 
        name: str, 
        include_tags: bool = False,
        include_costs: bool = False
    ) -> Dict[str, Any]:
        """Get a program by its name.
        Endpoint: GET /rest/asset/v1/program/byName.json
        
        Args:
            name: Name of the program
            include_tags: Set true to populate program tags
            include_costs: Set true to populate program costs
        
        Returns:
            Dictionary containing program details
        """
        path = "/rest/asset/v1/program/byName.json"
        params = {"name": name}
        if include_tags:
            params["includeTags"] = "true"
        if include_costs:
            params["includeCosts"] = "true"
        return self._request("GET", path, params=params)

    def clone_program(
        self, 
        program_id: int, 
        name: str,
        folder_id: int,
        folder_type: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """Clone an existing program.
        Endpoint: POST /rest/asset/v1/program/{id}/clone.json
        
        Args:
            program_id: The ID of the program to clone
            name: Name of the new program (max 255 characters)
            folder_id: ID of the folder to create the cloned program in
            folder_type: Type of folder (e.g., 'Folder' or 'Program')
            description: Optional description of the cloned program
        
        Returns:
            API response with cloned program details
        """
        path = f"/rest/asset/v1/program/{program_id}/clone.json"
        data = {
            "name": name,
            "folder": json.dumps({"id": folder_id, "type": folder_type})
        }
        if description:
            data["description"] = description
        return self._request_form("POST", path, data=data)

    # Token Update Functions
    def get_program_tokens(self, program_id: int) -> Dict[str, Any]:
        """Get My Tokens from a program.
        Endpoint: GET /rest/asset/v1/program/{id}/tokens.json
        
        Args:
            program_id: The Marketo program ID
        
        Returns:
            Dictionary containing program tokens
        """
        path = f"/rest/asset/v1/program/{program_id}/tokens.json"
        return self._request("GET", path)

    def update_program_tokens(self, program_id: int, tokens: Dict[str, str]) -> Dict[str, Any]:
        """Auto-populate My Tokens in a program.
        Endpoint: POST /rest/asset/v1/program/{id}/tokens.json
        
        Args:
            program_id: The Marketo program ID
            tokens: Dictionary mapping token names to values
        
        Returns:
            API response with updated token details
        """
        path = f"/rest/asset/v1/program/{program_id}/tokens.json"
        data = {}
        for token_name, value in tokens.items():
            data[f"tokens[{token_name}]"] = value
        return self._request_form("POST", path, data=data)

##--------------------------------------------------------------------------------------------------------------

    # Email Updates Functions
    def get_program_emails(self, program_id: int) -> Dict[str, Any]:
        """Get all email assets from a program.
        Endpoint: GET /rest/asset/v1/program/{id}/emails.json
        
        Args:
            program_id: The Marketo program ID
        
        Returns:
            Dictionary containing list of email assets in the program
        """
        path = f"/rest/asset/v1/program/{program_id}/emails.json"
        return self._request("GET", path)

    def get_email_content(self, email_id: int) -> Dict[str, Any]:
        """Get email content including subject line and body.
        Endpoint: GET /rest/asset/v1/email/{id}/content.json
        
        Args:
            email_id: The Marketo email asset ID
        
        Returns:
            Dictionary containing email content variables (subject, body, etc.)
        """
        path = f"/rest/asset/v1/email/{email_id}/content.json"
        return self._request("GET", path)

    def update_email_content(self, email_id: int, content_updates: Dict[str, str]) -> Dict[str, Any]:
        """Update email content variables like subject line and body.
        Endpoint: POST /rest/asset/v1/email/{id}/content.json
        
        Args:
            email_id: The Marketo email asset ID
            content_updates: Dictionary mapping content IDs to new values
        
        Returns:
            API response with updated email content details
        """
        path = f"/rest/asset/v1/email/{email_id}/content.json"
        data = {}
        for content_id, value in content_updates.items():
            data[f"content[{content_id}]"] = value
        return self._request_form("POST", path, data=data)

    def approve_email(self, email_id: int) -> Dict[str, Any]:
        """Approve an email asset.
        Endpoint: POST /rest/asset/v1/email/{id}/approveDraft.json
        
        Args:
            email_id: The Marketo email asset ID
        
        Returns:
            API response confirming email approval
        """
        path = f"/rest/asset/v1/email/{email_id}/approveDraft.json"
        return self._request_form("POST", path)

    # Landing Page Updates Functions
    def get_program_landing_pages(self, program_id: int) -> Dict[str, Any]:
        """Get all landing page assets from a program.
        Endpoint: GET /rest/asset/v1/program/{id}/landingPages.json
        
        Args:
            program_id: The Marketo program ID
        
        Returns:
            Dictionary containing list of landing page assets in the program
        """
        path = f"/rest/asset/v1/program/{program_id}/landingPages.json"
        return self._request("GET", path)

    def get_landing_page_content(self, landing_page_id: int) -> Dict[str, Any]:
        """Get landing page content sections.
        Endpoint: GET /rest/asset/v1/landingPage/{id}/content.json
        
        Args:
            landing_page_id: The Marketo landing page asset ID
        
        Returns:
            Dictionary containing landing page editable content sections
        """
        path = f"/rest/asset/v1/landingPage/{landing_page_id}/content.json"
        return self._request("GET", path)

    def update_landing_page_content(self, landing_page_id: int, content_updates: Dict[str, str]) -> Dict[str, Any]:
        """Update landing page editable sections, CTAs, banners, forms.
        Endpoint: POST /rest/asset/v1/landingPage/{id}/content.json
        
        Args:
            landing_page_id: The Marketo landing page asset ID
            content_updates: Dictionary mapping content section IDs to new values
        
        Returns:
            API response with updated landing page content details
        """
        path = f"/rest/asset/v1/landingPage/{landing_page_id}/content.json"
        data = {}
        for content_id, value in content_updates.items():
            data[f"content[{content_id}]"] = value
        return self._request_form("POST", path, data=data)

    def approve_landing_page(self, landing_page_id: int) -> Dict[str, Any]:
        """Approve a landing page asset.
        Endpoint: POST /rest/asset/v1/landingPage/{id}/approveDraft.json
        
        Args:
            landing_page_id: The Marketo landing page asset ID
        
        Returns:
            API response confirming landing page approval
        """
        path = f"/rest/asset/v1/landingPage/{landing_page_id}/approveDraft.json"
        return self._request_form("POST", path)

    # Smart Lists Functions
    def get_smart_list_rules(self, smart_list_id: int) -> Dict[str, Any]:
        """Get smart list filter rules.
        Endpoint: GET /rest/asset/v1/smartList/{id}/smartListRules.json
        
        Args:
            smart_list_id: The Marketo smart list ID
        
        Returns:
            Dictionary containing smart list filter rules and criteria
        """
        path = f"/rest/asset/v1/smartList/{smart_list_id}/smartListRules.json"
        return self._request("GET", path)

    def update_smart_list_rules(self, smart_list_id: int, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart list filter criteria.
        Endpoint: POST /rest/asset/v1/smartList/{id}/smartListRules.json
        
        Args:
            smart_list_id: The Marketo smart list ID
            rules: Dictionary containing new filter rules and criteria
        
        Returns:
            API response with updated smart list rules
        """
        path = f"/rest/asset/v1/smartList/{smart_list_id}/smartListRules.json"
        return self._request("POST", path, json=rules)

    # Smart Campaigns Functions
    def get_smart_campaign_rules(self, campaign_id: int) -> Dict[str, Any]:
        """Get smart campaign smart list rules.
        Endpoint: GET /rest/asset/v1/smartCampaign/{id}/smartListRules.json
        
        Args:
            campaign_id: The Marketo smart campaign ID
        
        Returns:
            Dictionary containing smart campaign filter rules
        """
        path = f"/rest/asset/v1/smartCampaign/{campaign_id}/smartListRules.json"
        return self._request("GET", path)

    def update_smart_campaign_rules(self, campaign_id: int, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart campaign filter criteria.
        Endpoint: POST /rest/asset/v1/smartCampaign/{id}/smartListRules.json
        
        Args:
            campaign_id: The Marketo smart campaign ID
            rules: Dictionary containing new filter rules and criteria
        
        Returns:
            API response with updated smart campaign rules
        """
        path = f"/rest/asset/v1/smartCampaign/{campaign_id}/smartListRules.json"
        return self._request("POST", path, json=rules)

    def get_smart_campaign_flow(self, campaign_id: int) -> Dict[str, Any]:
        """Get smart campaign flow steps.
        Endpoint: GET /rest/asset/v1/smartCampaign/{id}/flow.json
        
        Args:
            campaign_id: The Marketo smart campaign ID
        
        Returns:
            Dictionary containing smart campaign flow steps
        """
        path = f"/rest/asset/v1/smartCampaign/{campaign_id}/flow.json"
        return self._request("GET", path)

    def update_smart_campaign_flow(self, campaign_id: int, flow_steps: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart campaign flow based on requirements.
        Endpoint: POST /rest/asset/v1/smartCampaign/{id}/flow.json
        
        Args:
            campaign_id: The Marketo smart campaign ID
            flow_steps: Dictionary containing new flow steps and actions
        
        Returns:
            API response with updated smart campaign flow
        """
        path = f"/rest/asset/v1/smartCampaign/{campaign_id}/flow.json"
        return self._request("POST", path, json=flow_steps)

    def activate_smart_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Activate a smart campaign.
        Endpoint: POST /rest/asset/v1/smartCampaign/{id}/activate.json
        
        Args:
            campaign_id: The Marketo smart campaign ID
        
        Returns:
            API response confirming campaign activation
        """
        path = f"/rest/asset/v1/smartCampaign/{campaign_id}/activate.json"
        return self._request_form("POST", path)

    def schedule_smart_campaign(self, campaign_id: int, run_at: str, recipients: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Schedule a smart campaign to run at specified time.
        Endpoint: POST /rest/asset/v1/smartCampaign/{id}/schedule.json
        
        Args:
            campaign_id: The Marketo smart campaign ID
            run_at: ISO 8601 datetime string for when to run the campaign
            recipients: Optional dictionary containing recipient criteria
        
        Returns:
            API response confirming campaign scheduling
        """
        path = f"/rest/asset/v1/smartCampaign/{campaign_id}/schedule.json"
        data = {"runAt": run_at}
        if recipients:
            data.update(recipients)
        return self._request_form("POST", path, data=data)


