FROM python:3.10-slim

WORKDIR /app

# Copy all frontend files
COPY . .

# Expose port
EXPOSE 8080

ENV PORT=8080

# Run the server
CMD exec python server.py