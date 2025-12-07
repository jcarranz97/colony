# Local Development Setup

This guide walks you through setting up Colony for local development.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker and Docker Compose**
- **Git**

## Initial Setup

```bash
# Clone the repository
git clone https://github.com/jcarranz97/colony.git
cd colony

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

## Option 1: Docker Development (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### Services Available
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Option 2: Local Development

For development with hot reloading:

### Backend Setup

```bash
cd backend

# Install dependencies using uv
uv sync

# Run development server
uv run fastapi dev

# For linting and formatting
uv run ruff check . --fix    # Lint and auto-fix issues
uv run ruff format .         # Format code

# Run tests
uv run pytest
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Install development dependencies
npm install --save-dev prettier eslint

# Run development server
npm run dev
```

### Documentation Setup

```bash
cd docs

# Install MkDocs Material
pip install mkdocs-material

# Serve documentation
mkdocs serve
```

## Code Quality Setup

```bash
# Install pre-commit (if not already done)
pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files (first time)
pre-commit run --all-files
```

## Environment Variables

Create a `.env` file in the root directory:

```bash
# Database
DATABASE_URL=sqlite:///./colony.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Development
DEBUG=true
```

## Development Workflow

1. **Make changes** to your code
2. **Pre-commit hooks** will automatically run on commit
3. **Test locally** using Docker Compose or individual services
4. **Submit pull request** when ready

## Next Steps

- **[Code Quality](code-quality/)** - Learn about our code standards and pre-commit hooks
- **[Testing](testing/)** - Understand our testing approach
- **[Architecture](../architecture/)** - Explore the system design
