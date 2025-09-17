# Detailed Code Explanation: ADK Agent + MCP Server Architecture

## Overview

Your setup creates a **distributed AI agent system** where:
- **ADK Agent** (frontend) handles user interactions and orchestrates responses
- **MCP Server** (backend) exposes Marketo API operations as standardized tools
- **Communication** happens via HTTP Server-Sent Events (SSE) using the MCP protocol

## 1. MCP Server Architecture (`action_agent_server.py`)

### 1.1 Core Components

```python
from fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
```

**FastMCP**: A Python framework that simplifies creating MCP (Model Context Protocol) servers
**SseServerTransport**: Handles real-time communication via Server-Sent Events over HTTP

### 1.2 Business Logic Layer

```python
marketo = MarketoClient(client_id, client_secret, identity_base, rest_base)
agent = ActionAgent(marketo)
```

**Flow**: Configuration → MarketoClient → ActionAgent
- **MarketoClient**: Handles authentication, API calls, rate limiting to Marketo REST API
- **ActionAgent**: Business logic wrapper that provides higher-level operations

### 1.3 Tool Registration

```python
mcp = FastMCP(name="marketo-action-agent")

@mcp.tool()
def trigger_campaign(campaign_id: int, input_payload: dict) -> dict:
    return agent.trigger_campaign(campaign_id, input_payload)
```

**What happens here**:
1. `@mcp.tool()` decorator registers Python functions as MCP tools
2. FastMCP automatically generates **JSON schemas** for function signatures
3. Type hints (`int`, `dict`) become **parameter validation rules**
4. Docstrings become tool descriptions that the AI agent can understand

### 1.4 HTTP Server Setup

```python
sse = SseServerTransport("/messages")

async def handle_sse(request: Request):
    _server = mcp._mcp_server
    async with sse.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
        await _server.run(reader, writer, _server.create_initialization_options())
```

**Backend Communication Flow**:
1. **SSE Connection**: Client connects to `/sse` endpoint
2. **Protocol Handshake**: MCP initialization with capabilities exchange
3. **Bidirectional Communication**: 
   - Client → Server: Tool calls, requests
   - Server → Client: Tool responses, streaming data

### 1.5 Starlette Web Framework

```python
app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse, methods=["GET"]),     # SSE connections
    Mount("/messages", app=sse.handle_post_message),         # Message handling
])
```

**Route Architecture**:
- `/sse`: **Connection endpoint** - establishes persistent SSE connection
- `/messages`: **Message endpoint** - handles MCP protocol messages (tool calls, responses)

## 2. ADK Agent Architecture (`main_agent.py`)

### 2.1 Agent Configuration

```python
root_agent = Agent(
    model="gemini-2.5-flash",
    name="Marketo_autonomous_Engine",
    instruction="...",
    tools=[MCPToolset(connection_params=SseServerParams(url="http://localhost:8002/sse"))]
)
```

**Component Breakdown**:
- **model**: The LLM that powers decision-making and natural language understanding
- **instruction**: System prompt that defines the agent's behavior and capabilities
- **MCPToolset**: Connects to external MCP server and imports available tools
- **SseServerParams**: Specifies HTTP/SSE connection to MCP server

## 3. Backend Communication Protocol

### 3.1 MCP Protocol Flow

```
1. Connection Establishment:
   ADK Agent → GET /sse → MCP Server
   
2. Capability Exchange:
   Server: "I have tools: trigger_campaign, update_smart_list, get_campaign"
   Client: "I can call tools and handle responses"
   
3. Tool Discovery:
   ADK Agent requests available tools and their schemas
   MCP Server responds with JSON schemas for each tool
   
4. Runtime Tool Calls:
   User: "Trigger campaign 123 with lead data"
   ADK Agent: Analyzes request, identifies need for trigger_campaign tool
   ADK Agent → MCP Server: tool_call(trigger_campaign, {campaign_id: 123, ...})
   MCP Server → Marketo API: Execute campaign trigger
   MCP Server → ADK Agent: Success/failure response
   ADK Agent → User: Natural language response
```

### 3.2 Server-Sent Events (SSE) Details

**Why SSE over WebSockets?**
- **Simpler**: One-way server→client streaming with HTTP compatibility
- **Reliable**: Built-in reconnection and error handling
- **Firewall-friendly**: Works through corporate proxies

**SSE Message Format**:
```
data: {"type": "tool_call", "id": "123", "name": "trigger_campaign", "params": {...}}

data: {"type": "tool_response", "id": "123", "result": {...}}
```

## 4. Execution Flow Example

### User Query: "Trigger marketing campaign 456 for new leads"

**Step-by-Step Backend Process**:

1. **User Input Processing**:
   ```python
   # ADK Agent receives user message
   user_input = "Trigger marketing campaign 456 for new leads"
   ```

2. **LLM Analysis** (Gemini 2.5 Flash):
   ```
   System: Analyze user intent, identify required tools
   LLM Decision: Need to call trigger_campaign tool with campaign_id=456
   ```

3. **Tool Schema Lookup**:
   ```python
   # ADK Agent checks available tool signatures
   trigger_campaign(campaign_id: int, input_payload: dict) -> dict
   ```

4. **Parameter Construction**:
   ```python
   # ADK Agent constructs tool call
   tool_call = {
       "name": "trigger_campaign",
       "parameters": {
           "campaign_id": 456,
           "input_payload": {"source": "new_leads"}
       }
   }
   ```

5. **MCP Communication**:
   ```python
   # Via SSE to MCP Server
   POST /messages
   Content-Type: application/json
   
   {
       "type": "tool_call",
       "id": "uuid-123",
       "tool": "trigger_campaign",
       "params": {...}
   }
   ```

6. **MCP Server Processing**:
   ```python
   # MCP Server receives and routes to registered function
   def trigger_campaign(campaign_id: int, input_payload: dict):
       return agent.trigger_campaign(campaign_id, input_payload)
   
   # agent.trigger_campaign calls MarketoClient
   result = marketo.execute_campaign(campaign_id=456, leads=input_payload)
   ```

7. **Marketo API Call**:
   ```http
   POST https://your-instance.mktorest.com/rest/v1/campaigns/456/trigger.json
   Authorization: Bearer {token}
   Content-Type: application/json
   
   {"input": {"leads": [{"id": 12345}], "tokens": []}}
   ```

8. **Response Chain**:
   ```
   Marketo API → MarketoClient → ActionAgent → MCP Server → ADK Agent → User
   ```

9. **Natural Language Response**:
   ```python
   # ADK Agent processes tool result and generates response
   response = "Successfully triggered campaign 456 for new leads. The campaign will process the leads and execute the defined marketing actions."
   ```

## 5. Error Handling & Resilience

### 5.1 Connection Management
```python
# Auto-reconnection in SSE
async with sse.connect_sse(...) as (reader, writer):
    # Connection automatically retries on failure
```

### 5.2 Tool Execution Errors
```python
try:
    result = agent.trigger_campaign(campaign_id, input_payload)
    return result
except MarketoAPIError as e:
    return {"error": str(e), "type": "api_error"}
```

### 5.3 Type Validation
```python
def trigger_campaign(campaign_id: int, input_payload: dict) -> dict:
    # MCP automatically validates:
    # - campaign_id must be integer
    # - input_payload must be dictionary
    # - Return value must be dictionary
```

## 6. Scalability & Performance Considerations

### 6.1 Concurrent Connections
- **Starlette/Uvicorn**: Async server handles multiple ADK agents simultaneously
- **Connection Pooling**: Each agent maintains persistent SSE connection

### 6.2 Marketo API Management
- **Rate Limiting**: MarketoClient handles Marketo's API quotas
- **Token Management**: Automatic refresh of OAuth tokens
- **Request Queuing**: Prevents API overload

### 6.3 Memory Management
```python
# Each tool call is stateless
@mcp.tool()
def get_campaign(campaign_id: str) -> dict:
    # No shared state, scales horizontally
    return agent.get_campaign(campaign_id)
```

## 7. Security Considerations

### 7.1 Authentication Flow
```
ADK Agent → MCP Server → Marketo API
   ^            ^            ^
   |            |            |
No Auth    HTTP Only    OAuth 2.0
```

### 7.2 Network Security
- **Local Connection**: Default localhost:8002 (not exposed to internet)
- **No API Keys in Agent**: Credentials stored only in MCP server
- **Transport Security**: Can add HTTPS/TLS for production

This architecture provides a clean separation of concerns: ADK handles AI/UX, MCP server handles business logic/API integration, allowing for independent scaling and maintenance of each component.