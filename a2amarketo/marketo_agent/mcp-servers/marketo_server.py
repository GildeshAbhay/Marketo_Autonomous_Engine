"""
FastMCP server exposing ActionAgent as HTTP MCP tools.

Usage:
    python mcp_servers/action_agent_server.py

This starts a Starlette + Uvicorn server that exposes ActionAgent
methods as MCP-compatible tools over Server-Sent Events (SSE).
Your ADK Agent can then connect to: http://localhost:8002/sse
"""

import sys
import os
import yaml
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route, Mount

# Ensure repo root on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.marketo_client import MarketoClient
from utils.action_agent import ActionAgent

# Correct FastMCP import
from fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

# ------------------------------------------------------------------------------
# Load configuration
# ------------------------------------------------------------------------------

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
try:
    with open(CONFIG_PATH, "r") as fh:
        cfg = yaml.safe_load(fh)
except FileNotFoundError:
    cfg = {}

mcfg = cfg.get("settings", {}).get("marketo", {})

identity_base = mcfg.get("identity_base") or os.environ.get("MARKETO_IDENTITY_BASE")
rest_base = mcfg.get("rest_base") or os.environ.get("MARKETO_REST_BASE")
client_id = mcfg.get("client_id") or os.environ.get("MARKETO_CLIENT_ID")
client_secret = mcfg.get("client_secret") or os.environ.get("MARKETO_CLIENT_SECRET")

print("identity_base is", identity_base)

marketo = MarketoClient(client_id, client_secret, identity_base, rest_base)
agent = ActionAgent(marketo)

# ------------------------------------------------------------------------------
# Create FastMCP and register tools
# ------------------------------------------------------------------------------

mcp = FastMCP(name="marketo-action-agent")

@mcp.tool()
def trigger_campaign(campaign_id: int, input_payload: dict) -> dict:
    """
    Trigger a Marketo campaign by ID.

    Args:
        campaign_id: The ID of the Marketo campaign.
        input_payload: Dictionary of parameters to send.

    Returns:
        API response from Marketo.
    """
    return agent.trigger_campaign(campaign_id, input_payload)

@mcp.tool()
def update_smart_list(smart_list_id: int, payload: dict) -> dict:
    """
    Update a Marketo Smart List.

    Args:
        smart_list_id: ID of the Smart List to update.
        payload: Fields to update.

    Returns:
        API response from Marketo.
    """
    return agent.update_smart_list(smart_list_id, payload)

@mcp.tool()
def get_campaign(campaign_id: str) -> dict:
    """
    Retrieve details about a specific Marketo campaign.

    Args:
        campaign_id: The campaign ID.

    Returns:
        Campaign details as a dictionary.
    """
    return agent.get_campaign(campaign_id)

# ToDo: Added in Future
# @mcp.tool()
# def get_campaign_details(campaign_id: int) -> dict:
#     return agent.get_campaign_details(campaign_id)

# @mcp.tool()
# def get_smart_list(smart_list_id: int) -> dict:
#     return agent.get_smart_list(smart_list_id)

# ------------------------------------------------------------------------------
# SSE transport and Starlette app (FIXED)
# ------------------------------------------------------------------------------

# Create SSE transport with the correct endpoint
sse = SseServerTransport("/messages")

async def handle_sse(request: Request):
    """
    Handle incoming SSE connection from an MCP client.
    """
    _server = mcp._mcp_server
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send,
    ) as (reader, writer):
        await _server.run(reader, writer, _server.create_initialization_options())

# Create Starlette app with proper routes
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),  # SSE endpoint
        Mount("/messages", app=sse.handle_post_message),      # Message handling
    ],
)

# ------------------------------------------------------------------------------
# Run server
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Use uvicorn directly instead of mcp.run() for better control
    uvicorn.run(app, host="localhost", port=8002, log_level="info")