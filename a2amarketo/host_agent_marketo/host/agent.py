import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterable, List

import httpx
import nest_asyncio
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
)
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# from .marketo_tools import (
#     create_smart_list,
#     find_leads,
#     trigger_campaign,
#     get_marketo_assets,
# )
from .remote_agent_connection import RemoteAgentConnections
import os
from google.genai import types as genai_types
from google import genai

load_dotenv()
nest_asyncio.apply()


class HostAgent:
    """The Host agent."""

    def __init__(
        self,
    ):
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ""
        self._agent = self.create_agent()
        self._user_id = "host_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        # Initialize Gemini client for RBAC
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            self._gemini_client = genai.Client(api_key=api_key)
        else:
            print("⚠️ Warning: No GEMINI_API_KEY found, RBAC checks will fail")
            self._gemini_client = None

    async def _async_init_components(self, remote_agent_addresses: List[str]):
        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                card_resolver = A2ACardResolver(client, address)
                try:
                    card = await card_resolver.get_agent_card()
                    remote_connection = RemoteAgentConnections(
                        agent_card=card, agent_url=address
                    )
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                except httpx.ConnectError as e:
                    print(f"ERROR: Failed to get agent card from {address}: {e}")
                except Exception as e:
                    print(f"ERROR: Failed to initialize connection for {address}: {e}")

        agent_info = [
            json.dumps({"name": card.name, "description": card.description})
            for card in self.cards.values()
        ]
        print("agent_info:", agent_info)
        self.agents = "\n".join(agent_info) if agent_info else "No friends found"

    @classmethod
    async def create(
        cls,
        remote_agent_addresses: List[str],
    ):
        instance = cls()
        await instance._async_init_components(remote_agent_addresses)
        return instance

    def create_agent(self) -> Agent:
        return Agent(
            model="gemini-2.5-flash",
            name="Host_Agent",
            instruction=self.root_instruction,
            description="This Host agent orchestrates Marketo operations with specialized agents.",
            tools=[
                self.check_rbac_permission,  # Add this new tool
                self.send_message,
                # create_smart_list,
                # find_leads,
                # trigger_campaign,
                # get_marketo_assets,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        return f"""
         **Role:** You are the Host Agent, an expert coordinator for Marketo operations with role-based access control (RBAC).

        **Core Directives:**

        *   **RBAC First:** ALWAYS check permissions using check_rbac_permission BEFORE delegating to Marketo agents.
        *   **Permission Check Flow:**
            1. User sends a query
            2. You MUST call check_rbac_permission(user_query, user_role, tool_context) FIRST
            3. If permission is GRANTED, proceed with send_message to the appropriate agent
            4. If permission is DENIED, inform the user they lack permission and DO NOT call send_message
        
        *   **Delegate to Agents:** After RBAC check passes, use send_message to communicate with specialized agents.
        *   **Agent Communication:** Use send_message with agent_name "Marketo Campaign Agent" for Marketo-related requests.
        *   **Summarize Results:** When agents return data, provide clear, concise summaries.
        *   **Handle Errors:** If RBAC denies permission or agents return errors, explain clearly to the user.

        **Important Rules:**
        - NEVER skip the RBAC check for Marketo operations
        - Analysts can only READ data (view, list, get, show, etc.)
        - Analysts CANNOT write/modify/trigger/update/create/delete in Marketo
        - Admins have full access to all operations

        **Available Tools:**
        1. check_rbac_permission(user_query, user_role, tool_context): Check if user has permission for the query
        2. send_message(agent_name, task, tool_context): Send requests to specialized agents (only after RBAC check)

        **Today's Date (YYYY-MM-DD):** {datetime.now().strftime("%Y-%m-%d")}

        <Available Agents>
        {self.agents}
        </Available Agents>

        **CRITICAL: Response Formatting Instructions**
        
        You MUST format ALL your responses using clean, semantic HTML. Follow these rules strictly:
        
        1. **Headings**: Use <h3>, <h4> for section titles
           Example: <h3>Campaign Details</h3>
        
        2. **Bold/Strong text**: Use <strong> for important values and labels
           Example: <strong>ID:</strong> 12345
        
        3. **Lists**: Use <ul> and <li> for bullet points
           Example:
           <ul>
               <li>Item 1</li>
               <li>Item 2</li>
           </ul>
        
        4. **Key-Value Pairs**: Format data using <strong> for keys
           Example:
           <p><strong>Email:</strong> user@example.com</p>
           <p><strong>Created:</strong> 2025-01-15</p>
        
        5. **Tables**: Use proper HTML tables for structured data
           Example:
           <table>
               <thead>
                   <tr>
                       <th>Campaign ID</th>
                       <th>Name</th>
                       <th>Status</th>
                   </tr>
               </thead>
               <tbody>
                   <tr>
                       <td>123</td>
                       <td>Email Campaign</td>
                       <td>Active</td>
                   </tr>
               </tbody>
           </table>
        
        6. **Paragraphs**: Use <p> for regular text
        
        7. **Line breaks**: Use <br> for line breaks within paragraphs
        
        8. **Code/IDs**: Use <code> for technical identifiers
           Example: Campaign ID: <code>4567</code>
        
        9. **Emphasis**: Use <em> for subtle emphasis
        
        10. **Sections**: Use <div> with clear structure when grouping related content
        
        **Response Format Example:**
        
        <h3>Lead Details for ID 6266</h3>
        <p><strong>ID:</strong> 6266</p>
        <p><strong>Email:</strong> saurabht+113@grazitti.com</p>
        <p><strong>Created At:</strong> 2019-05-03T16:17:19Z</p>
        <p><strong>Updated At:</strong> 2025-05-21T06:58:07Z</p>
        <p><strong>Status:</strong> Active</p>

        **Example Flow:**
        User (analyst): "Update campaign 4567 name to Test Campaign"
        Step 1: check_rbac_permission("Update campaign 4567 name to Test Campaign", "analyst", tool_context)
        Result: DENIED - analysts cannot update campaigns
        Response: "<p><strong>⚠️ Permission Denied</strong></p><p>You are an analyst and can only perform read operations. Updating campaigns requires admin privileges.</p>"

        User (admin): "Get campaign details for id 4567"
        Step 1: check_rbac_permission("Get campaign details for id 4567", "admin", tool_context)
        Result: GRANTED
        Step 2: send_message("Marketo Campaign Agent", "get campaign details for id 4567", tool_context)
        Response: "<h3>Campaign Details</h3><p><strong>ID:</strong> 4567</p><p><strong>Name:</strong> Summer Campaign 2025</p><p><strong>Status:</strong> Active</p>"
        
        **REMEMBER:** 
        - Always use HTML tags in your responses
        - Never use plain text formatting like ** for bold or - for bullets
        - Keep HTML clean and semantic
        - Don't use inline styles (CSS is handled separately)
        """

    async def check_rbac_permission(
        self, 
        user_query: str, 
        user_role: str, 
        tool_context: ToolContext
    ) -> dict:
        """
        Check if user has permission to perform the requested operation based on RBAC rules.
        
        Args:
            user_query: The user's natural language query
            user_role: The user's role (admin or analyst)
            tool_context: Tool context for accessing conversation history
            
        Returns:
            Dictionary with permission status and details
        """
        # Valid roles
        ROLE_ADMIN = "admin"
        ROLE_ANALYST = "analyst"
        
        # Validate role
        if user_role not in [ROLE_ADMIN, ROLE_ANALYST]:
            return {
                "permission": "DENIED",
                "reason": f"Invalid role: {user_role}",
                "can_proceed": False
            }
        
        # Admins can do anything
        if user_role == ROLE_ADMIN:
            return {
                "permission": "GRANTED",
                "reason": "Admin has full access to all operations",
                "can_proceed": True,
                "intent": "admin_override"
            }
        
        # For analysts, classify the query intent using Gemini
        try:
            intent = await self._classify_query_intent_with_context(
                user_query, 
                tool_context
            )
            
            if intent == "write":
                return {
                    "permission": "DENIED",
                    "reason": (
                        "This query requires write/modify permissions. "
                        "Analysts can only perform read operations (view, list, get, show). "
                        "Operations like trigger, update, create, delete require admin privileges."
                    ),
                    "can_proceed": False,
                    "intent": intent
                }
            else:
                return {
                    "permission": "GRANTED",
                    "reason": "Read operation permitted for analyst role",
                    "can_proceed": True,
                    "intent": intent
                }
                
        except Exception as e:
            print(f"❌ Error in RBAC check: {e}")
            # Fail-safe: deny on error
            return {
                "permission": "DENIED",
                "reason": f"RBAC check failed due to error: {str(e)}",
                "can_proceed": False
            }
    
    async def _classify_query_intent_with_context(
        self, 
        query: str, 
        tool_context: ToolContext
    ) -> str:
        """
        Classify query intent (read vs write) using Gemini API with conversation context.
        
        Args:
            query: The user's query
            tool_context: Tool context for accessing conversation history
            
        Returns:
            "read" or "write"
        """
        if not self._gemini_client:
            print("⚠️ No Gemini client available, defaulting to 'read' for safety")
            return "read"
        
        # Get conversation history for context
        conversation_context = ""
        if tool_context and hasattr(tool_context, 'conversation_history'):
            # Build context from recent conversation
            recent_messages = tool_context.conversation_history[-5:]  # Last 5 messages
            conversation_context = "\n".join([
                f"{msg.role}: {msg.content}" 
                for msg in recent_messages
            ])
        
        prompt = f"""Analyze the following user query and determine if it represents a READ or WRITE operation in a marketing automation system (Marketo).

**Current Query:** "{query}"

**Conversation Context:**
{conversation_context if conversation_context else "No previous conversation context"}

**Classification Guidelines:**

**WRITE operations** include:
- Triggering, executing, running, activating, launching, or firing campaigns
- Creating new campaigns, smart lists, leads, programs, or assets
- Updating, modifying, changing, editing, or renaming existing campaigns, smart lists, or leads
- Deleting or removing campaigns, smart lists, leads, or assets
- Sending, scheduling, or dispatching emails or campaigns
- Adding or removing leads from lists or programs
- Activating, deactivating, enabling, or disabling campaigns or programs
- Approving or unapproving emails, landing pages, or assets

**READ operations** include:
- Getting, fetching, retrieving, viewing, or showing information
- Listing, searching, or filtering data
- Generating reports or analytics
- Describing or explaining assets or configurations
- Checking status or viewing history
- Any query that only retrieves or displays information without modifying data

Consider the conversation context to understand references like "it", "that campaign", "the same one", etc.

Return your analysis as a JSON object:
{{
  "intent": "read" or "write",
  "confidence": "high" or "medium" or "low",
  "reasoning": "brief explanation considering the context"
}}

**Important:** Only return valid JSON. The "intent" field must be exactly "read" or "write" (lowercase).
"""

        try:
            response = self._gemini_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=256,
                    response_mime_type="application/json",
                )
            )
            
            result = json.loads(response.text)
            intent = result.get("intent", "").lower()
            
            if intent not in ["read", "write"]:
                print(f"⚠️ Invalid intent from Gemini: {intent}. Defaulting to 'read'")
                return "read"
            
            confidence = result.get("confidence", "unknown")
            reasoning = result.get("reasoning", "No reasoning provided")
            print(f"🤖 RBAC Intent Classification: {intent} (confidence: {confidence})")
            print(f"   Reasoning: {reasoning}")
            
            return intent
            
        except Exception as e:
            print(f"❌ Error in Gemini classification: {e}")
            # Fail-safe: default to read
            return "read"

    async def stream(
        self, query: str, session_id: str, user_role: str = "analyst", file_path: str = None
    ) -> AsyncIterable[dict[str, Any]]:
        """
        Streams the agent's response to a given query.
        
        Args:
            query: User's query
            session_id: Session ID for conversation tracking
            user_role: User's role (admin or analyst) - defaults to analyst for safety
            file_path: Optional file path for file-based operations (e.g., bulk import)
        """
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        
        # Include user role and file path in the query context
        enriched_query = f"[USER_ROLE: {user_role}]\n{query}"
        if file_path:
            enriched_query += f"\n[FILE_PATH: {file_path}]"
        
        content = types.Content(
            role="user", 
            parts=[types.Part.from_text(text=enriched_query)]
        )
        
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={"user_role": user_role},  # Store role in session state
                session_id=session_id,
            )
        
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "The host agent is thinking...",
                }

    async def send_message(self, agent_name: str, task: str, tool_context: ToolContext):
        """Sends a task to a remote friend agent."""
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} not found")
        client = self.remote_agent_connections[agent_name]

        if not client:
            raise ValueError(f"Client not available for {agent_name}")

        # Generate unique message ID for this request
        message_id = str(uuid.uuid4())
        
        # FIXED: Don't include taskId and contextId - let the remote agent create them
        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
                # Removed: "taskId" and "contextId"
            },
        }

        message_request = SendMessageRequest(
            id=message_id, params=MessageSendParams.model_validate(payload)
        )
        
        try:
            send_response: SendMessageResponse = await client.send_message(message_request)
            print(f"send_response root type: {type(send_response.root)}")
            print(f"send_response: {send_response}")

            if not isinstance(send_response.root, SendMessageSuccessResponse):
                error_msg = f"Received a non-success response: {send_response.root}"
                print(error_msg)
                return [{"error": error_msg}]

            if not isinstance(send_response.root.result, Task):
                error_msg = f"Response result is not a Task: {type(send_response.root.result)}"
                print(error_msg)
                return [{"error": error_msg}]

            task_result = send_response.root.result
            response_content = task_result.model_dump_json(exclude_none=True)
            json_content = json.loads(response_content)
            print(f"json_content after task result: {json_content}")
            resp = []
            if json_content.get("artifacts"):
                for artifact in json_content["artifacts"]:
                    if artifact.get("parts"):
                        for part in artifact["parts"]:
                            if part.get("text"):
                                resp.append({"text": part["text"]})
                            else:
                                resp.append(part)
            
            return resp if resp else [{"message": "Task completed successfully but no content returned"}]
            
        except Exception as e:
            error_msg = f"Error sending message to {agent_name}: {str(e)}"
            print(error_msg)
            return [{"error": error_msg}]


def _get_initialized_host_agent_sync():
    """Synchronously creates and initializes the HostAgent."""

    async def _async_main():
        # Hardcoded URLs for the Marketo agents
        marketo_agent_urls = [
            "http://localhost:10002",  # Marketo Agent
             "http://localhost:10003",  # Web Search Agent
        ]

        print("initializing host agent")
        hosting_agent_instance = await HostAgent.create(
            remote_agent_addresses=marketo_agent_urls
        )
        print("HostAgent initialized")
        return hosting_agent_instance.create_agent()

    try:
        return asyncio.run(_async_main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            print(
                f"Warning: Could not initialize HostAgent with asyncio.run(): {e}. "
                "This can happen if an event loop is already running (e.g., in Jupyter). "
                "Consider initializing HostAgent within an async function in your application."
            )
        else:
            raise


root_agent = _get_initialized_host_agent_sync()
