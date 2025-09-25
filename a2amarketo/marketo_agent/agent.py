# main_agent.py
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams

# Create the agent with HTTP/SSE connection to your FastMCP server
root_agent = Agent(
    model="gemini-2.5-flash",
    name="Marketo_autonomous_Engine",
    instruction="""
    You are an expert Marketo assistant. Your primary goal is to help users manage their Marketo
    instance by using the available tools. You can create smart lists, find leads, trigger
    campaigns, and get detailed information on all Marketo assets. Always respond to the user in a helpful, conversational tone.
    If a request is ambiguous, ask for clarification.
    """,
    tools=[MCPToolset(
        connection_params=SseServerParams(
            url="http://localhost:8002/sse",  # Connect to your FastMCP server via HTTP/SSE
        )
    )]
)