FROM python:3.13-slim

WORKDIR /app

# Copy dependencies
COPY ../pyproject.toml ../uv.lock ./
COPY ../utils /app/utils
COPY . .

# Install uv and dependencies
RUN pip install uv && uv sync

# Expose port
EXPOSE 8080

# Run the MCP server
CMD python marketo_server.py