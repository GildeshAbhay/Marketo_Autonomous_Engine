FROM python:3.10-slim

WORKDIR /app

# Copy deployment config (needed by shared/config_loader.py)
COPY deployment_config.json /app/deployment_config.json

# Copy shared config
COPY shared /app/shared

# Copy requirements.txt from root
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy frontend code
COPY frontend /app/frontend

# Expose port
EXPOSE 8080

ENV PORT=8080

# Run the server using module syntax from /app directory
CMD ["python", "-m", "frontend.server"]