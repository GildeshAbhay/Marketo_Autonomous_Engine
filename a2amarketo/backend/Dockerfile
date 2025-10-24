FROM python:3.10-slim

WORKDIR /app

# Copy shared config first
COPY ../shared /app/shared

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose port (Cloud Run sets PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/api/health')"

# Run the app with proper host binding
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1