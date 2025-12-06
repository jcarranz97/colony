# Colony

A personal expense management application built with FastAPI and Next.js.

## Overview

Colony is a full-stack web application designed to help you track and manage your personal expenses efficiently. Built as a monorepo for simplicity, it combines a FastAPI backend with a sleek Next.js frontend.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js with NextUI
- **Documentation**: MkDocs Material
- **Containerization**: Docker & Docker Compose
- **Architecture**: Monorepo structure

## Project Structure

```
colony/
├── backend/          # FastAPI application
│   ├── app/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # Next.js application  
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── shared/           # Shared types, constants
├── docs/            # Documentation
├── docker-compose.yml
└── README.md
```

## Features (Planned)

- 📊 Expense tracking and categorization
- 📈 Financial analytics and insights
- 💳 Multi-account support
- 📱 Responsive web interface
- 🔒 Secure authentication
- 📊 Data visualization
- 💾 Data export capabilities

## Prerequisites

- Docker and Docker Compose
- Node.js (for local development)
- Python 3.11+ (for local development)

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/your-username/colony.git
cd colony
```

2. Start the application:
```bash
docker-compose up --build
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

#### Documentation

```bash
cd docs
pip install mkdocs-material
mkdocs serve
```

## API Documentation

The API documentation is automatically generated using FastAPI's built-in Swagger UI. Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Workflow

1. Create feature branches from `main`
2. Make your changes
3. Test locally using Docker Compose
4. Submit a pull request

## Project Goals

This project serves multiple purposes:
- **Personal Finance Management**: Create a robust tool for tracking personal expenses
- **Technology Practice**: Explore modern web development technologies
- **Learning Experience**: Implement best practices in full-stack development

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Setup basic project structure
- [ ] Implement authentication system
- [ ] Create expense CRUD operations
- [ ] Build responsive frontend
- [ ] Add data visualization
- [ ] Implement category management
- [ ] Add export functionality
- [ ] Create comprehensive documentation

## Contact

For questions or suggestions, please open an issue in the repository.

---

**Note**: This project is currently in development. Features and documentation will be updated as the project progresses.