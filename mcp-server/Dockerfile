FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv==0.5.21

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only (deterministic, locked)
RUN uv sync --no-dev --frozen

# Copy application code
COPY . .

EXPOSE 8002

CMD ["uv", "run", "python", "-m", "colony_mcp.server"]
