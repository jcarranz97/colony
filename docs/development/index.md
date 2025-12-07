# Development Guide

Welcome to the Colony development guide. This section contains all the information you need to contribute to or modify the Colony project.

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
├── .github/         # GitHub Actions workflows
├── docker-compose.yml
└── README.md
```

## Development Philosophy

This project serves multiple purposes:

- **Personal Finance Management**: Create a robust tool for tracking personal expenses
- **Technology Practice**: Explore modern web development technologies
- **Learning Experience**: Implement best practices in full-stack development

## Prerequisites for Development

- **Docker and Docker Compose** (required)
- **Node.js 18+** (for local frontend development)
- **Python 3.11+** (for local backend development)
- **Git** (version control)

## Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/jcarranz97/colony.git
   cd colony
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow coding standards
   - Write tests for new features
   - Update documentation

4. **Test Locally**
   ```bash
   docker-compose up --build
   ```

5. **Submit Pull Request**
   - Ensure all tests pass
   - Include clear description
   - Reference any related issues

## Next Steps

- **[Local Setup](setup/)** - Set up your development environment
- **[Code Quality](code-quality/)** - Code standards and pre-commit hooks
- **[Testing](testing/)** - Learn about our testing approach
- **[Deployment](deployment/)** - Understand deployment processes (including docs)
- **[Architecture](../architecture/)** - Dive into system design
