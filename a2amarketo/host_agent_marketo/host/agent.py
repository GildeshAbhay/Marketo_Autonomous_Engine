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

from .marketo_tools import (
    create_smart_list,
    find_leads,
    trigger_campaign,
    get_marketo_assets,
)
from .remote_agent_connection import RemoteAgentConnections

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
                self.send_message,
                # create_smart_list,
                # find_leads,
                # trigger_campaign,
                # get_marketo_assets,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        return f"""
         **Role:** You are the Host Agent, an expert coordinator for Marketo operations. Your primary function is to delegate requests to specialized Marketo agents and provide clear summaries.

        **Core Directives:**

        *   **Delegate to Agents:** When users ask for Marketo information (campaigns, smart lists, leads), use the send_message tool to communicate with the appropriate agent.
        *   **Agent Communication:** Use send_message with agent_name "Marketo Campaign Agent" for all Marketo-related requests.
        *   **Summarize Results:** When agents return data, provide clear, concise summaries.
        *   **Handle Errors:** If agents return errors, explain the issue clearly to the user.
        *   **Tool Usage:** Always use the send_message tool to get information from Marketo agents. Do not generate Marketo data on your own.

        **Available Tools:**
        - send_message(agent_name, task, tool_context): Send requests to specialized agents

        **Today's Date (YYYY-MM-DD):** {datetime.now().strftime("%Y-%m-%d")}

        <Available Agents>
        {self.agents}
        </Available Agents>

        **Example Usage:**
        User: "get me the campaign detail for id 4567"
        You should: send_message("Marketo Campaign Agent", "get me the campaign detail for id 4567", tool_context)
        """

    async def stream(
        self, query: str, session_id: str
    ) -> AsyncIterable[dict[str, Any]]:
        """
        Streams the agent's response to a given query.
        """
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
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

        # Generate unique IDs for this request
        # task_id = str(uuid.uuid4())
        # context_id = str(uuid.uuid4())
        # message_id = str(uuid.uuid4())

        state = tool_context.state
        task_id = state.get("task_id", str(uuid.uuid4()))
        context_id = state.get("context_id", str(uuid.uuid4()))
        message_id = str(uuid.uuid4())
        
        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
                "taskId": task_id,
                "contextId": context_id,
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
            # "http://localhost:10003",  # Web Search Agent
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
