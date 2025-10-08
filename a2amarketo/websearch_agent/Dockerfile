FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY . .

# Copy shared config
COPY ../shared /app/shared

# Install dependencies
RUN uv sync

# Expose port
EXPOSE 8080

# Run the agent
CMD uv run --active .