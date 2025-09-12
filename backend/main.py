# backend/main.py
"""
FastAPI backend - lightweight bridge between frontend and MCP/Agents.
Routes:
  POST /query  -> route to Data Agent (GET-like ops)
  POST /action -> route to Action Agent (trigger/update)
  GET  /history -> returns recent memory from sqlite_memory
"""

import os, json, time, requests, sys
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# local utils
from config import settings
from memory.sqlite_memory import save_query, fetch_recent_queries, initialize_db
# Attempt to import agents for direct invocation fallback
try:
    from agents.data_agent import DataAgent
    from agents.action_agent import ActionAgent
    from utils.marketo_client import MarketoClient
    DIRECT_AGENT_AVAILABLE = True
except Exception:
    DIRECT_AGENT_AVAILABLE = False

app = FastAPI(title="Marketo MCP POC Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# configuration: MCP HTTP ports (use same keys as config/config.yaml)
DATA_AGENT_PORT = os.getenv("DATA_AGENT_PORT", str(settings.get("mcp", {}).get("data_agent_port", "8001")))
ACTION_AGENT_PORT = os.getenv("ACTION_AGENT_PORT", str(settings.get("mcp", {}).get("action_agent_port", "8002")))

# Simple request models
class CommandPayload(BaseModel):
    command: str
    payload: Optional[Dict[str, Any]] = None

def _call_mcp_http(port: str, tool: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Call an MCP server over HTTP.
    This is a conservative generic format: POST http://localhost:{port}/tool
    body: { "tool": "<tool_name>", "args": { ... } }
    Note: If your FastMCP exposes a different HTTP contract, update this accordingly.
    """
    url = f"http://127.0.0.1:{port}/tool"
    body = {"tool": tool, "args": args or {}}
    try:
        r = requests.post(url, json=body, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise

def _direct_agent_call(agent_type: str, command: str, payload: Optional[Dict[str, Any]] = None):
    """
    Fallback: call local agent classes (if available).
    Commands are basic heuristics; you can replace with proper parser.
    """
    if not DIRECT_AGENT_AVAILABLE:
        raise RuntimeError("Direct agent invocation not available in this environment.")
    client = MarketoClient()
    if agent_type == "data":
        agent = DataAgent(client)
        # naive parsing: commands like "get_campaign_details 123"
        parts = command.strip().split()
        if parts[0].lower() in ("get_campaign_details", "get_campaign", "campaign"):
            campaign_id = int(parts[-1])
            return agent.get_campaign_details(campaign_id)
        if parts[0].lower() in ("get_smart_list", "smartlist"):
            sl_id = int(parts[-1])
            return agent.get_smart_list(sl_id)
        # generic: return error
        raise ValueError("Unrecognized data command")
    else:
        agent = ActionAgent(MarketoClient())
        parts = command.strip().split()
        if parts[0].lower() in ("trigger_campaign", "trigger"):
            campaign_id = int(parts[-1])
            return agent.trigger_campaign(campaign_id, payload or {})
        if parts[0].lower() in ("update_smart_list", "update"):
            sl_id = int(parts[-1])
            return agent.update_smart_list(sl_id, payload or {})
        raise ValueError("Unrecognized action command")


@app.on_event("startup")
def startup_event():
    # ensure memory DB exists
    initialize_db()


@app.post("/query")
async def query_route(cmd: CommandPayload):
    """
    Route a 'query' command to Data Agent.
    Preference: MCP HTTP call. Fallback: direct agent call.
    """
    ts = int(time.time())
    save_query(ts, "in", {"command": cmd.command, "payload": cmd.payload}, {"type": "query"})

    # example tool name - your MCP servers must map tools accordingly
    tool_name = "get_campaign_details"  # for simple POC; in prod parse command to tool mapping
    try:
        # try MCP HTTP
        try:
            resp = _call_mcp_http(DATA_AGENT_PORT, tool_name, {"raw_command": cmd.command, "payload": cmd.payload})
            save_query(int(time.time()), "out", resp, {"via": "mcp_http"})
            return resp
        except Exception:
            # fallback to direct agent call
            resp = _direct_agent_call("data", cmd.command, cmd.payload)
            save_query(int(time.time()), "out", resp, {"via": "direct_agent"})
            return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/action")
async def action_route(cmd: CommandPayload):
    """
    Route an 'action' command to Action Agent (trigger/update).
    """
    ts = int(time.time())
    save_query(ts, "in", {"command": cmd.command, "payload": cmd.payload}, {"type": "action"})
    tool_name = "trigger_campaign"  # default mapping, adjust by parsing
    try:
        try:
            resp = _call_mcp_http(ACTION_AGENT_PORT, tool_name, {"raw_command": cmd.command, "payload": cmd.payload})
            save_query(int(time.time()), "out", resp, {"via": "mcp_http"})
            return resp
        except Exception:
            resp = _direct_agent_call("action", cmd.command, cmd.payload)
            save_query(int(time.time()), "out", resp, {"via": "direct_agent"})
            return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def history(limit: int = 20):
    rows = fetch_recent_queries(limit)
    return {"count": len(rows), "items": rows}
