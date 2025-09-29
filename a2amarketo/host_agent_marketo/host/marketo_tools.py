import os
from typing import Dict, List, Any
import json
import sys

# Add the marketo_agent directory to the path to import MarketoClient
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'marketo_agent'))
from marketo_client import MarketoClient

def get_marketo_client() -> MarketoClient:
    """Initialize Marketo client from environment variables."""
    client_id = os.getenv("MARKETO_CLIENT_ID")
    client_secret = os.getenv("MARKETO_CLIENT_SECRET")
    identity_base = os.getenv("MARKETO_IDENTITY_BASE")
    rest_base = os.getenv("MARKETO_REST_BASE")
    
    if not all([client_id, client_secret, identity_base, rest_base]):
        raise ValueError("Missing required Marketo environment variables: MARKETO_CLIENT_ID, MARKETO_CLIENT_SECRET, MARKETO_IDENTITY_BASE, MARKETO_REST_BASE")
    
    return MarketoClient(client_id, client_secret, identity_base, rest_base)


def create_smart_list(name: str, description: str, folder_id: int = 1) -> dict:
    """
    Creates a smart list in Marketo.

    Args:
        name: The name of the smart list to create.
        description: Description of the smart list.
        folder_id: ID of the folder to create the smart list in (default: 1).

    Returns:
        A dictionary with the creation status and details.
    """
    try:
        client = get_marketo_client()
        response = client.create_smart_list(name, description, folder_id)
        
        if response.get("result"):
            smart_list = response["result"][0]  # Marketo returns array
            return {
                "status": "success",
                "message": f"Smart list '{name}' created successfully.",
                "smart_list_id": smart_list.get("id"),
                "name": name,
                "description": description,
                "folder_id": folder_id
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to create smart list: {response.get('errors', 'Unknown error')}",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create smart list: {str(e)}",
        }


def find_leads(filter_type: str = "email", filter_values: str = "", limit: int = 100) -> dict:
    """
    Searches for leads in Marketo based on specified criteria.

    Args:
        filter_type: Type of filter to apply (email, id, etc.).
        filter_values: Comma-separated values to filter by.
        limit: Maximum number of leads to return (default: 100).

    Returns:
        A dictionary with search results and lead information.
    """
    try:
        client = get_marketo_client()
        
        # Parse filter values
        filter_list = [v.strip() for v in filter_values.split(",") if v.strip()] if filter_values else []
        
        if filter_list:
            response = client.get_leads(filter_type=filter_type, filter_values=filter_list)
        else:
            # Get all leads (this might be limited by Marketo API)
            response = client.get_leads()
        
        if not response.get("result"):
            return {
                "status": "success",
                "message": "No leads found matching criteria.",
                "leads": [],
                "total_count": 0,
                "filter_type": filter_type,
                "filter_values": filter_values
            }
        
        leads = response["result"][:limit]  # Limit results
        
        return {
            "status": "success",
            "message": f"Found {len(leads)} leads matching criteria.",
            "leads": leads,
            "total_count": len(leads),
            "filter_type": filter_type,
            "filter_values": filter_values
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to search leads: {str(e)}",
        }


def trigger_campaign(campaign_id: int, lead_ids: str) -> dict:
    """
    Triggers a marketing campaign in Marketo.

    Args:
        campaign_id: ID of the campaign to trigger.
        lead_ids: Comma-separated list of lead IDs to target.

    Returns:
        A dictionary with campaign trigger status.
    """
    try:
        client = get_marketo_client()
        
        # Parse lead IDs
        lead_id_list = [int(id.strip()) for id in lead_ids.split(",") if id.strip()]
        
        if not lead_id_list:
            return {
                "status": "error",
                "message": "No valid lead IDs provided.",
            }
        
        # Prepare payload for Marketo API
        payload = {
            "input": [{"id": lead_id} for lead_id in lead_id_list]
        }
        
        response = client.trigger_campaign(campaign_id, payload)
        
        if response.get("result"):
            return {
                "status": "success",
                "message": f"Campaign {campaign_id} triggered successfully.",
                "campaign_id": campaign_id,
                "lead_count": len(lead_id_list),
                "response": response
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to trigger campaign: {response.get('errors', 'Unknown error')}",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to trigger campaign: {str(e)}",
        }


def get_marketo_assets(asset_type: str = "all", limit: int = 50) -> dict:
    """
    Retrieves information about Marketo assets.

    Args:
        asset_type: Type of assets to retrieve (campaigns, smart_lists, etc.).
        limit: Maximum number of assets to return.

    Returns:
        A dictionary with asset information.
    """
    try:
        client = get_marketo_client()
        all_assets = []
        
        if asset_type in ["all", "campaigns"]:
            try:
                campaigns_response = client.get_campaigns(max_return=limit)
                if campaigns_response.get("result"):
                    for campaign in campaigns_response["result"]:
                        all_assets.append({
                            "id": campaign.get("id"),
                            "name": campaign.get("name"),
                            "type": "campaign",
                            "status": campaign.get("status"),
                            "description": campaign.get("description", ""),
                            "created_date": campaign.get("createdAt", ""),
                            "updated_date": campaign.get("updatedAt", "")
                        })
            except Exception as e:
                print(f"Error retrieving campaigns: {e}")
        
        if asset_type in ["all", "smart_lists"]:
            try:
                smart_lists_response = client.get_smart_lists(max_return=limit)
                if smart_lists_response.get("result"):
                    for smart_list in smart_lists_response["result"]:
                        all_assets.append({
                            "id": smart_list.get("id"),
                            "name": smart_list.get("name"),
                            "type": "smart_list",
                            "status": smart_list.get("status"),
                            "description": smart_list.get("description", ""),
                            "created_date": smart_list.get("createdAt", ""),
                            "updated_date": smart_list.get("updatedAt", "")
                        })
            except Exception as e:
                print(f"Error retrieving smart lists: {e}")
        
        return {
            "status": "success",
            "message": f"Retrieved {len(all_assets)} {asset_type} assets.",
            "assets": all_assets,
            "total_count": len(all_assets),
            "asset_type": asset_type
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve assets: {str(e)}",
        }
