FROM python:3.13-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared config
COPY ../shared /app/shared

# Copy backend code
COPY . .

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Run the app
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}