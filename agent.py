# main_agent.py
from google.adk.agents import Agent
# from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
import asyncio
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams

# async def init_tools():
#     # Create the toolset via constructor (if from_server not available)
#     toolset = MCPToolset(connection_params=SseServerParams(
#         url="http://localhost:8002/sse",
#     ))
#     # Hypothetical method to fetch tools & exit stack
#     tools = await toolset.get_tools()
#     return tools

# tools = asyncio.run(init_tools())
root_agent = Agent(
    model="gemini-2.5-flash",  # Or another powerful LLM
    name="Marketo_autonomous_Engine",
    instruction="""
    You are an expert Marketo assistant. Your primary goal is to help users manage their Marketo
    instance by using the available tools. You can create smart lists, find leads, trigger
    campaigns, and get detailed information on all Marketo assets. Always respond to the user in a helpful, conversational tone.
    If a request is ambiguous, ask for clarification.
    """,
    tools=[MCPToolset(
        connection_params=StdioServerParameters(
            command="python",
            args=[
                 "C:/Users/saksham.dubey/Desktop/Python Projects/POCs/MCP-Agent/Marketo_Autonomous_Engine/mcp-servers/action_agent_server.py"
            ],
        )
        # tool_filter=['list_tables'] # Optional: ensure only specific tools are loaded C:\Users\saksham.dubey\Desktop\Python Projects\POCs\MCP-Agent\Marketo_Autonomous_Engine\mcp-servers\action_agent_server.py "C:\Users\saksham.dubey\Desktop\Python Projects\POCs\MCP-Agent\Marketo_Autonomous_Engine\mcp-servers\action_agent_server.py"#
    )]  # The agent now has access to all tools on the MCP server
)
# # Start the chat interface
# if __name__ == "__main__":
#     # try:
#     agent.run()
# # finally:
# #     asyncio.run(exit_stack.aclose())