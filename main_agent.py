# main_agent.py
from google.adk.agent import Agent
from google.adk.tools import MCPTool

# Connect to the Marketo MCP Server you built.
marketo_mcp_tool = MCPTool("http://localhost:8000")

agent = Agent(
    model="gemini-1.5-pro-latest",  # Or another powerful LLM
    name="Marketo-Assistant-Agent",
    instruction="""
    You are an expert Marketo assistant. Your primary goal is to help users manage their Marketo
    instance by using the available tools. You can create smart lists, find leads, trigger
    campaigns, and get detailed information on all Marketo assets. Always respond to the user in a helpful, conversational tone.
    If a request is ambiguous, ask for clarification.
    """,
    tools=[marketo_mcp_tool]  # The agent now has access to all tools on the MCP server
)

# Start the chat interface
if __name__ == "__main__":
    agent.run_as_app() # Or agent.run_in_terminal()