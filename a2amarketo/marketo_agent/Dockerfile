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

# Copy marketo_agent module with all subdirectories
COPY marketo_agent /app/marketo_agent

# Expose port
EXPOSE 8080

# Run the agent using module syntax from /app directory
CMD ["python", "-m", "marketo_agent.__main__"]