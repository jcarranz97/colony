# Local Development Setup

This guide walks you through setting up Colony for local development.

## Prerequisites

- **Python 3.13+**
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
# Start all services (with hot reload enabled)
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### Services Available
- **Backend API**: http://localhost:8000
- **API Documentation (Swagger UI)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Hot Reload

The backend service mounts the `backend/` directory as a volume, so any code
changes you make locally are reflected immediately inside the container —
no restart needed. FastAPI's development server (`fastapi dev`) watches for
file changes and reloads automatically.

## Seed Data

The repository ships with a `seed_data.yaml` file at the project root. When
you run `docker-compose up`, a one-time `seeder` service automatically creates
the database schema and populates it with initial development data, so you can
log in and start using the app immediately without making any manual API calls.

### Default dev credentials

| Field    | Value              |
|----------|--------------------|
| Email    | `dev@colony.local` |
| Password | `colony123`        |

These credentials are ready to use as-is for local development. If you prefer
your own, edit `seed_data.yaml` **before** running `docker-compose up` for the
first time.

### YAML structure

```yaml
users:
  - email: user@example.com
    password: plaintext-password   # hashed with Argon2ID at seed time
    first_name: First
    last_name: Last
    preferred_currency: USD        # USD | MXN
    locale: en-US
    payment_methods:
      - name: US Bank Debit
        method_type: debit         # debit | credit | cash | transfer
        default_currency: USD      # USD | MXN
        description: Optional note
```

### Re-seeding manually

The seed script is **idempotent** — running it again skips records that already
exist. Use this to pick up new entries you add to `seed_data.yaml`:

```bash
docker-compose run --rm seeder
```

Or locally (outside Docker):

```bash
cd backend
DATABASE_URL=postgresql://colony_user:colony_password@localhost:5432/colony_db \
  SEED_FILE=../seed_data.yaml \
  uv run python scripts/seed_db.py
```

### Starting fresh

By default, `docker-compose down` stops and removes containers but **keeps
the `postgres_data` volume**, so your database survives restarts. This is
intentional for day-to-day development — you don't lose your work every time
you restart Docker.

To wipe all data and re-seed from scratch, add the `-v` flag:

```bash
docker-compose down -v          # removes the postgres_data volume
docker-compose up -d --build    # recreates schema + seeds automatically
```

Use `-v` when you need a truly clean slate, for example after modifying
`seed_data.yaml` or testing a schema change.

---

## Option 2: Local Development (without Docker)

For running the backend directly on your machine without Docker:

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

# Type checking
uv run pyright .

# Run tests
uv run pytest
```

## Managing Dependencies

### Adding Dependencies

We use [uv](https://docs.astral.sh/uv/) for Python package management:

```bash
cd backend

# Add a production dependency
uv add fastapi

# Add a development dependency
uv add pytest --dev
uv add ruff --dev

# Add a dependency with version constraints
uv add "fastapi>=0.100.0"

# Add from a specific index or source
uv add requests --index-url https://pypi.org/simple/
```

### Removing Dependencies

```bash
# Remove a dependency
uv remove package-name

# Remove a dev dependency
uv remove package-name --dev
```

### Updating Dependencies

```bash
# Update all dependencies
uv sync --upgrade

# Update a specific package
uv add package-name --upgrade

# See outdated packages
uv tree --outdated
```

### Installing Dependencies

```bash
# Install all dependencies (production + dev)
uv sync

# Install only production dependencies
uv sync --no-dev

# Install and update lock file
uv sync --upgrade
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
2. **Add dependencies** if needed using `uv add`
3. **Pre-commit hooks** will automatically run on commit
4. **Test locally** using Docker Compose or individual services
5. **Submit pull request** when ready

## Next Steps

- **[Code Quality](code-quality/)** - Learn about our code standards and pre-commit hooks
- **[Testing](testing/)** - Understand our testing approach
- **[Architecture](../architecture/)** - Explore the system design
