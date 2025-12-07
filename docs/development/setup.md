# Local Development Setup

This guide walks you through setting up Colony for local development.

## Option 1: Docker Development (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/your-username/colony.git
cd colony

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

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

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

## Development Tools

### Recommended VS Code Extensions
- Python
- Pylance
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- Docker

### Code Formatting
```bash
# Backend (Python)
pip install black isort flake8
black backend/
isort backend/

# Frontend (JavaScript/TypeScript)
npm install -g prettier
prettier --write frontend/src/
```

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Kill process using port 8000
sudo lsof -t -i:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

**Docker Build Issues**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**Frontend Dependencies**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf frontend/node_modules
cd frontend && npm install
```