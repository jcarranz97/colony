FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv==0.5.21

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps in production; dev included here for testing)
RUN uv sync --no-dev --frozen

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]
