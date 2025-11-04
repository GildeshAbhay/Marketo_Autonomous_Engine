FROM python:3.13-slim

WORKDIR /app

# Copy deployment config (needed by shared/config_loader.py)
COPY deployment_config.json /app/deployment_config.json

# Copy shared config
COPY shared /app/shared

# Copy requirements.txt from root
COPY requirements.txt /app/requirements.txt

# Install all dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy marketo_agent module (includes mcp-servers and utils)
COPY marketo_agent /app/marketo_agent

# Expose port
EXPOSE 8080

# Run the MCP server directly (can't use -m with hyphenated directory)
CMD ["python", "marketo_agent/mcp-servers/marketo_server.py"]