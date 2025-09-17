import time
import requests
from typing import Any, Dict, Optional

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

    def _ensure_token(self) -> str:
        now = time.time()
        if self._access_token and now < (self._token_expiry - 30):
            return self._access_token

        token_url = f"{self.identity_base}/oauth/token"
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
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"{self.rest_base}{path}"
        resp = requests.request(method, url, params=params, json=json, headers=headers, timeout=15)
        resp.raise_for_status()
        # Marketo responses usually wrap results in a 'result' field; return raw json for now
        return resp.json()


    # -- Example helper methods (adjust endpoints for the fields you need) --
    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Fetch campaign asset details.
        Endpoint pattern: GET /rest/asset/v1/smartCampaign/{id}.json
        """
        path = f"/asset/v1/smartCampaign/{campaign_id}.json"
        return self._request("GET", path)


    def get_smart_list(self, smart_list_id: int) -> Dict[str, Any]:
        """Fetch a smart list asset.
        Endpoint pattern: GET /rest/asset/v1/smart/list/{id}.json
        """
        path = f"/rest/asset/v1/smart/list/{smart_list_id}.json"
        return self._request("GET", path)


    def get_campaign_members(self, campaign_id: int, offset: int = 0, max_return: int = 200) -> Dict[str, Any]:
        """Example: list members for a campaign (if applicable) - adapt as needed.
        This is illustrative; you may need different endpoints for campaign results or lead lists.
        """
        # Marketo endpoints vary; adapt to the exact API you need.
        path = f"/rest/v1/campaigns/{campaign_id}/members.json"
        params = {"offset": offset, "maxReturn": max_return}
        return self._request("GET", path, params=params)


    def trigger_campaign(self, campaign_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a campaign. Example endpoint: POST /rest/v1/campaigns/{id}/trigger.json
        payload should follow Marketo trigger payloads (e.g., {'input': [{'id': leadId}]})
        """
        path = f"/rest/v1/campaigns/{campaign_id}/trigger.json"
        return self._request("POST", path, json=payload)


    def update_smart_list(self, smart_list_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update smart list (if your flow supports updating via REST) - adapt as needed."""
        path = f"/rest/asset/v1/smart/list/{smart_list_id}.json"
        return self._request("POST", path, json=payload)



