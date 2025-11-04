import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.config_loader import get_config

deployment_config = get_config()

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from .agent import create_agent
from .agent_executor import MarketoAgentExecutor
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass

def main():
    """Starts the agent server."""
    # host = "localhost"
    # port = 10002

    service_name = "marketo_agent"  # or "websearch_agent"
    # host = deployment_config.get_service_host(service_name)
    # port = deployment_config.get_service_port(service_name)
    host = os.getenv("HOST", "0.0.0.0")
    port = deployment_config.get_service_port(service_name)

    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
            if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError(
                    "GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
                )

        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="marketo_operations",
            name="Marketo Operations",
            description="Manages Marketo campaigns, smart lists, leads, and other marketing automation tasks.",
            tags=["marketo", "marketing", "automation"],
            examples=["Show me all campaigns", "Create a smart list for high-value leads", "Find leads with score above 80" , "give me the details for campaign id 4567"],
        )
        agent_card = AgentCard(
            name="Marketo Campaign Agent",
            description="An agent that manages Marketo campaigns, smart lists, leads, and marketing automation.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            capabilities=capabilities,
            skills=[skill],
        )

        adk_agent = create_agent()
        runner = Runner(
            app_name=agent_card.name,
            agent=adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        agent_executor = MarketoAgentExecutor(runner)

        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        uvicorn.run(server.build(), host=host, port=port)
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
