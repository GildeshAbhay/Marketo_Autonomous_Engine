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
from dotenv import load_dotenv
load_dotenv()
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

identity_base = mcfg.get("identity_base") or os.getenv("MARKETO_IDENTITY_BASE")
rest_base = mcfg.get("rest_base") or os.getenv("MARKETO_REST_BASE")
client_id = mcfg.get("client_id") or os.getenv("MARKETO_CLIENT_ID")
client_secret = mcfg.get("client_secret") or os.getenv("MARKETO_CLIENT_SECRET")

print("identity_base is", identity_base)

marketo = MarketoClient(client_id, client_secret, identity_base, rest_base)
agent = ActionAgent(marketo)

# ------------------------------------------------------------------------------
# Create FastMCP and register tools
# ------------------------------------------------------------------------------

# mcp = FastMCP(name="marketo-action-agent")


# response = agent.trigger_campaign(campaign_id, input_payload)
# print(f"Response get campaign : {response}")

# response = agent.update_smart_list(smart_list_id, payload)
# print(f"Response update smart list : {response}")

response = agent.get_campaign(campaign_id = "10965")
print(f"Response get campaign : {response}")

# response = agent.get_lead_by_id(lead_id = 6228, fields=["id", "email", "firstName", "lastName", "company"])
# print(f"Response get lead by id : {response}")

response = agent.update_smart_campaign(smart_campaign_id = 10965, payload = {"description": "Change name description testing 1"})
print(f"Response update smart campaign : {response}")

# response = agent.get_leads_by_filter_type(filter_type, filter_values, fields, batch_size)
# print(f"Response get leads by filter type : {response}")

# response = agent.describe_lead()
# print(f"Response describe lead : {response}")

# response = agent.get_lead_partitions()
# print(f"Response get lead partitions : {response}")

# response = agent.get_leads_by_program(program_id, fields, batch_size)
# print(f"Response get leads by program : {response}")

# response = agent.get_leads_by_smart_list(smart_list_id, fields, batch_size, next_page_token)
# print(f"Response get leads by smart list : {response}")
