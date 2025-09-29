# A2A Marketo Demo

This document describes a multi-agent application demonstrating how to orchestrate conversations between different agents to manage Marketo operations and marketing automation.

This application contains three agents:
*   **Host Agent**: The primary agent that orchestrates Marketo operations and coordinates with specialized agents.
*   **Marketo Agent**: An agent that handles core Marketo operations like campaigns, smart lists, and lead management.
*   **Web Search Agent**: An agent that provides web search capabilities and research insights for marketing automation.

## Setup and Deployment

### Prerequisites

Before running the application locally, ensure you have the following installed:

1. **uv:** The Python package management tool used in this project. Follow the installation guide: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
2. **python 3.13** Python 3.13 is required to run a2a-sdk 
3. **set up .env** 

Create a `.env` file in the root of the `a2amarketo` directory with your API keys:
```
GOOGLE_API_KEY="your_google_api_key_here"
MARKETO_CLIENT_ID="your_marketo_client_id"
MARKETO_CLIENT_SECRET="your_marketo_client_secret"
MARKETO_IDENTITY_BASE="https://your-instance.mktorest.com/identity"
MARKETO_REST_BASE="https://your-instance.mktorest.com/rest"
```

## Run the Agents

You will need to run each agent in a separate terminal window. The first time you run these commands, `uv` will create a virtual environment and install all necessary dependencies before starting the agent.

### Terminal 1: Run Marketo Agent
```bash
cd marketo_agent
uv venv
source .venv/bin/activate
uv run --active .
```

### Terminal 2: Run Web Search Agent
```bash
cd websearch_agent
uv venv
source .venv/bin/activate
uv run --active .
```

### Terminal 3: Run Host Agent
```bash
cd host_agent_marketo
uv venv
source .venv/bin/activate
uv run --active adk web      
```

## Interact with the Host Agent

Once all agents are running, the host agent will begin coordinating Marketo operations. You can view the interaction in the terminal output of the `host_agent`.

## Agent Capabilities

### Host Agent
- Orchestrates Marketo operations using real Marketo API
- Delegates tasks to specialized agents
- Provides direct Marketo tools (create smart lists, find leads, trigger campaigns)
- Coordinates responses from multiple agents

### Marketo Agent
- Manages Marketo campaigns and their status using real API calls
- Creates and manages smart lists via Marketo REST API
- Searches and filters leads using Marketo's lead API
- Provides information about Marketo assets

### Web Search Agent
- Searches for Marketo-related resources and best practices
- Provides competitor analysis
- Offers learning resources and tutorials
- Analyzes marketing automation trends

## References
- https://github.com/google/a2a-python
- https://codelabs.developers.google.com/intro-a2a-purchasing-concierge#1
