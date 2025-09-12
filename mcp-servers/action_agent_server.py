"""
FastMCP server exposing ActionAgent as HTTP MCP tools.
Run: python mcp_servers/action_agent_server.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastmcp import FastMCP
import os, yaml
from marketo_client import MarketoClient
from agents.action_agent import ActionAgent

# Load config
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

if ADK_AVAILABLE:
    adk_agent = make_adk_action_agent(marketo)  # Creates ADKAgent
    # Wire ADK tools: Use ADK's tool registration to expose ActionAgent methods
    adk_agent.add_tool(trigger_campaign)  # Adjust per ADK docs; e.g., adk_agent.tools.register(...)

mcp = FastMCP(name="marketo-action-agent")

@mcp.tool()
def trigger_campaign(campaign_id: int, input_payload: dict) -> dict:
    return agent.trigger_campaign(campaign_id, input_payload)

@mcp.tool()
def update_smart_list(smart_list_id: int, payload: dict) -> dict:
    return agent.update_smart_list(smart_list_id, payload)

@mcp.tool()
def get_campaign(campaign_id: str) -> dict:
    return agent.get_campaign(campaign_id)

if __name__ == "__main__":
    # Run HTTP MCP server on port 8002
    mcp.run(transport="http", port=8002)
