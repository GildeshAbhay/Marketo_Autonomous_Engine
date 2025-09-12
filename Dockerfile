# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080 # Vertex AI default port

CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8080"]