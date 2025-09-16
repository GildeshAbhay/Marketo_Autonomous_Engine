"""
FastMCP server exposing DataAgent as HTTP MCP tools.
Run: python mcp_servers/data_agent_server.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastmcp import FastMCP
import os, yaml
from marketo_client import MarketoClient
from agents.data_agent import DataAgent

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
try:
    with open(CONFIG_PATH, "r") as fh:
        cfg = yaml.safe_load(fh)
except FileNotFoundError:
    cfg = {}

cfg = cfg.get("settings", {})
mcfg = cfg.get("marketo", {})
identity_base = mcfg.get("identity_base") or os.environ.get("MARKETO_IDENTITY_BASE")
rest_base = mcfg.get("rest_base") or os.environ.get("MARKETO_REST_BASE")
client_id = mcfg.get("client_id") or os.environ.get("MARKETO_CLIENT_ID")
client_secret = mcfg.get("client_secret") or os.environ.get("MARKETO_CLIENT_SECRET")

marketo = MarketoClient(client_id, client_secret, identity_base, rest_base)
agent = DataAgent(marketo)
mcp = FastMCP(name="marketo-data-agent")

@mcp.tool()
def get_campaign_details(campaign_id: int) -> dict:
    return agent.get_campaign_details(campaign_id)

@mcp.tool()
def get_smart_list(smart_list_id: int) -> dict:
    return agent.get_smart_list(smart_list_id)

if __name__ == "__main__":
    # Run HTTP MCP server on port 8001
    mcp.run(transport="http", host="0.0.0.0", port=8001)
