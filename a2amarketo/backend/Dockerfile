FROM python:3.10-slim

WORKDIR /app

# Copy deployment config (needed by shared/config_loader.py)
COPY deployment_config.json /app/deployment_config.json

# Copy shared config
COPY shared /app/shared

# Copy host_agent_marketo (needed by backend)
COPY host_agent_marketo /app/host_agent_marketo

# Copy requirements.txt from root level FIRST
COPY requirements.txt /app/requirements.txt

# Install all dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code
COPY backend /app/backend

# Expose port (Cloud Run sets PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:${PORT:-8080}/api/health')"

# Run the app using module syntax from /app directory
CMD ["python", "-m", "backend.app"]