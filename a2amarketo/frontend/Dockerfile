FROM python:3.13-slim

WORKDIR /app

# Copy all frontend files
COPY . .

# Expose port
EXPOSE 8080

# Run the server (update server.py to use PORT env var)
CMD python server.py