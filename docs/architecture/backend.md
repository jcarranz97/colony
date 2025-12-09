# Backend Architecture

Colony's backend follows a modular, domain-driven architecture using FastAPI with clear separation of concerns and industry best practices.

## Architecture Overview

The backend is built using **FastAPI** with a **domain-driven design** approach, where each business domain (auth, expenses, cycles, etc.) is organized as a self-contained module with its own models, schemas, services, and routes.

### Key Principles

- **Domain-Driven Design**: Each business domain is a separate module
- **Separation of Concerns**: Clear boundaries between layers (routes, services, data)
- **Dependency Injection**: Clean dependency management
- **Type Safety**: Full type annotations with Pydantic
- **Testing**: Comprehensive test coverage per domain

## Project Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── app/                        # Main application source
│   ├── auth/                   # Authentication domain
│   │   ├── router.py           # Auth API routes
│   │   ├── schemas.py          # Pydantic request/response models
│   │   ├── models.py           # SQLAlchemy database models
│   │   ├── dependencies.py     # Auth-specific dependencies
│   │   ├── service.py          # Authentication business logic
│   │   ├── config.py           # Auth configuration (JWT settings)
│   │   ├── constants.py        # Auth constants and error codes
│   │   ├── exceptions.py       # Auth-specific exceptions
│   │   └── utils.py            # Auth utility functions
│   ├── payment_methods/        # Payment methods domain
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   ├── service.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   ├── expense_templates/      # Expense templates domain
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   ├── service.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   ├── cycles/                 # Cycle management domain
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   ├── service.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   ├── expenses/               # Individual expenses domain
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   ├── service.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   ├── reports/                # Analytics and reporting domain
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   ├── exchange_rates/         # Currency exchange domain
│   │   ├── client.py           # External API client
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── service.py
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   ├── config.py               # Global application configuration
│   ├── database.py             # Database connection and session management
│   ├── models.py               # Global database models and base classes
│   ├── exceptions.py           # Global exception classes
│   ├── dependencies.py         # Global dependencies (DB session, current user)
│   ├── pagination.py           # Pagination utilities
│   └── main.py                 # FastAPI application factory
├── tests/                      # Test suite organized by domain
│   ├── auth/
│   ├── payment_methods/
│   ├── expense_templates/
│   ├── cycles/
│   ├── expenses/
│   ├── reports/
│   ├── exchange_rates/
│   ├── conftest.py            # Pytest configuration and fixtures
│   └── utils.py               # Test utilities
├── .env                       # Environment variables
├── alembic.ini                # Alembic configuration
├── pyproject.toml             # Project configuration and dependencies
└── README.md
```

## Domain Architecture

Each domain follows a consistent internal structure with clear responsibilities:

### File Responsibilities

#### router.py
Contains all HTTP endpoints for the domain. Handles request/response, validation, and delegates business logic to services.

```python
# Example: app/cycles/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.auth.models import User
from . import service, schemas

router = APIRouter(prefix="/cycles", tags=["cycles"])

@router.post("/", response_model=schemas.CycleResponse)
async def create_cycle(
    cycle_data: schemas.CycleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await service.create_cycle(db, cycle_data, current_user.id)
```

#### schemas.py
Pydantic models for request/response validation and serialization.

```python
# Example: app/cycles/schemas.py
from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

class CycleCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    income_amount: Decimal
    generate_from_templates: bool = True

class CycleResponse(BaseModel):
    id: str
    name: str
    start_date: date
    end_date: date
    income_amount: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
```

#### models.py
SQLAlchemy database models representing the domain's data structure.

```python
# Example: app/cycles/models.py
from sqlalchemy import Column, String, Date, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.models import BaseModel, CycleStatus

class Cycle(BaseModel):
    __tablename__ = "cycles"

    name = Column(String(100), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    income_amount = Column(DECIMAL(10, 2), default=0)
    status = Column(ENUM(CycleStatus), default=CycleStatus.DRAFT)

    # Relationships
    user = relationship("User", back_populates="cycles")
    expenses = relationship("CycleExpense", back_populates="cycle")
```

#### service.py
Contains the domain's business logic, data processing, and complex operations.

```python
# Example: app/cycles/service.py
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from ..expense_templates import service as template_service
from ..expenses import service as expense_service

async def create_cycle(
    db: Session,
    cycle_data: schemas.CycleCreate,
    user_id: str
) -> models.Cycle:
    """Create a new cycle and optionally generate expenses from templates."""

    # Create cycle
    cycle = models.Cycle(
        name=cycle_data.name,
        user_id=user_id,
        start_date=cycle_data.start_date,
        end_date=cycle_data.end_date,
        income_amount=cycle_data.income_amount
    )

    db.add(cycle)
    db.flush()  # Get cycle ID

    # Generate expenses from templates if requested
    if cycle_data.generate_from_templates:
        await _generate_expenses_from_templates(db, cycle)

    db.commit()
    return cycle
```

#### dependencies.py
Domain-specific dependencies for dependency injection.

```python
# Example: app/cycles/dependencies.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.auth.models import User
from . import service
from .constants import ErrorCode

async def get_cycle_by_id(
    cycle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dependency to get cycle by ID and verify ownership."""
    cycle = await service.get_cycle_by_id(db, cycle_id, current_user.id)
    if not cycle:
        raise HTTPException(
            status_code=404,
            detail=ErrorCode.CYCLE_NOT_FOUND
        )
    return cycle
```

#### constants.py
Domain-specific constants, error codes, and enums.

```python
# Example: app/cycles/constants.py
from enum import Enum

class ErrorCode:
    CYCLE_NOT_FOUND = "CYCLE_NOT_FOUND"
    CYCLE_ALREADY_COMPLETED = "CYCLE_ALREADY_COMPLETED"
    INVALID_CYCLE_DATES = "INVALID_CYCLE_DATES"
    CYCLE_NAME_EXISTS = "CYCLE_NAME_EXISTS"

class CycleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"

# Business constants
MAX_CYCLE_DURATION_DAYS = 45
DEFAULT_CYCLE_DURATION_DAYS = 42  # 6 weeks
```

#### exceptions.py
Domain-specific exception classes.

```python
# Example: app/cycles/exceptions.py
from app.exceptions import AppException
from .constants import ErrorCode

class CycleNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            error_code=ErrorCode.CYCLE_NOT_FOUND,
            message="Cycle not found",
            status_code=404
        )

class CycleAlreadyCompletedException(AppException):
    def __init__(self):
        super().__init__(
            error_code=ErrorCode.CYCLE_ALREADY_COMPLETED,
            message="Cannot modify completed cycle",
            status_code=409
        )
```

#### utils.py
Domain-specific utility functions that don't contain business logic.

```python
# Example: app/cycles/utils.py
from datetime import date, timedelta
from typing import Tuple

def calculate_cycle_dates(start_date: date) -> Tuple[date, date]:
    """Calculate 6-week cycle end date from start date."""
    end_date = start_date + timedelta(days=42)  # 6 weeks
    return start_date, end_date

def format_cycle_name(start_date: date, end_date: date) -> str:
    """Generate a descriptive cycle name from dates."""
    return f"{start_date.strftime('%B %Y')} Cycle"
```

## Global Architecture Components

### app/main.py
Application factory that initializes FastAPI with all domain routers.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.auth.router import router as auth_router
from app.cycles.router import router as cycles_router
from app.expenses.router import router as expenses_router
# ... other routers

def create_app() -> FastAPI:
    app = FastAPI(
        title="Colony API",
        version="1.0.0",
        description="Personal expense management API"
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include domain routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(cycles_router, prefix="/api/v1")
    app.include_router(expenses_router, prefix="/api/v1")

    return app

app = create_app()
```

### app/database.py
Database connection and session management.

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### app/models.py
Base model classes and global models.

```python
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)
```

### app/dependencies.py
Global dependencies used across domains.

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import service as auth_service

security = HTTPBearer()

async def get_current_user(
    token: str = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user from JWT token."""
    user = await auth_service.get_user_from_token(db, token.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user
```

## Cross-Domain Communication

When domains need to interact, they import services explicitly:

```python
# In app/cycles/service.py
from app.expense_templates import service as template_service
from app.expenses import service as expense_service
from app.exchange_rates import service as exchange_service

async def create_cycle_with_expenses(db: Session, cycle_data: schemas.CycleCreate):
    # Get user's templates
    templates = await template_service.get_active_templates(db, cycle_data.user_id)

    # Generate expenses for each template
    for template in templates:
        expenses = await expense_service.generate_from_template(
            db, template, cycle_data.start_date, cycle_data.end_date
        )

        # Convert currencies if needed
        for expense in expenses:
            if expense.currency != "USD":
                usd_amount = await exchange_service.convert_to_usd(
                    expense.amount, expense.currency
                )
                expense.amount_usd = usd_amount
```

## Data Flow Architecture

```mermaid
graph TD
    A[HTTP Request] --> B[Router Layer]
    B --> C[Pydantic Validation]
    C --> D[Dependency Injection]
    D --> E[Service Layer]
    E --> F[Database Models]
    F --> G[SQLAlchemy ORM]
    G --> H[PostgreSQL]

    E --> I[External Services]
    I --> J[Exchange Rate APIs]

    E --> K[Cross-Domain Services]
    K --> L[Other Domain Services]

    H --> G
    G --> F
    F --> E
    E --> M[Response Schemas]
    M --> N[HTTP Response]
```

## Key Architecture Benefits

### 1. **Modularity**
- Each domain is self-contained
- Easy to add new features without affecting other domains
- Clear boundaries and responsibilities

### 2. **Testability**
- Each layer can be tested independently
- Mock dependencies easily
- Domain-specific test suites

### 3. **Maintainability**
- Consistent structure across domains
- Easy to locate and modify code
- Clear separation of concerns

### 4. **Scalability**
- Domains can be extracted to microservices if needed
- Independent development by different teams
- Horizontal scaling capabilities

### 5. **Type Safety**
- Full type annotations
- Pydantic validation
- SQLAlchemy type mapping

## Authentication & Security

### JWT Authentication
The application uses JSON Web Tokens (JWT) for stateless authentication:

```python
# app/auth/config.py
class AuthSettings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_prefix = "AUTH_"
```

### Token Flow
1. User authenticates via `/auth/login` with email/password
2. System returns JWT token with user claims
3. Client includes token in `Authorization: Bearer <token>` header
4. System validates token on protected endpoints

### Password Security
- Passwords hashed using **Argon2ID** algorithm
- Minimum 8 characters required
- Salt automatically generated per password

```python
# app/auth/utils.py
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def hash_password(password: str) -> str:
    """Hash password using Argon2ID."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
```

### Authentication Dependencies
Global authentication handled via dependency injection:

```python
# app/dependencies.py
from app.auth.dependencies import get_current_active_user

# Use in any protected endpoint
@router.get("/protected")
async def protected_endpoint(
    current_user: CurrentActiveUser  # Automatically validates JWT
):
    return {"user": current_user.email}
```

## Error Handling Architecture

### Exception Hierarchy
Structured exception handling with consistent error responses:

```python
# app/exceptions.py
class AppException(Exception):
    """Base application exception."""

    def __init__(self, error_code: str, message: str, status_code: int = 400, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

# Domain-specific exceptions inherit from AppException
class UserNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            error_code="USER_NOT_FOUND",
            message="User not found",
            status_code=404
        )
```

### Global Exception Handlers
Centralized error handling for consistent API responses:

```python
# app/exceptions.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

async def app_exception_handler(request: Request, exc: AppException):
    """Handle application-specific exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

async def validation_exception_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "details": {}
            }
        }
    )
```

### Error Response Format
All errors follow a consistent structure:

```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found",
    "details": {
      "user_id": "123e4567-e89b-12d3-a456-426614174000"
    }
  }
}
```

## Database Architecture

### Connection Management
PostgreSQL connection using SQLAlchemy with connection pooling:

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Connection pool configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,           # Verify connections before use
    pool_recycle=300,             # Recycle connections every 5 minutes
    pool_size=10,                 # Connection pool size
    max_overflow=20               # Additional connections if needed
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### Migration Strategy
Database versioning using Alembic:

```bash
# Generate migration
alembic revision --autogenerate -m "add user table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Model Conventions
Consistent database modeling patterns:

```python
# app/models.py
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields and behaviors."""
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

## Validation & Serialization

### Pydantic Models
Type-safe request/response handling:

```python
# Domain schemas follow naming conventions
class UserCreate(BaseModel):      # For POST requests
    email: EmailStr
    password: str
    first_name: Optional[str]

class UserUpdate(BaseModel):      # For PUT/PATCH requests
    first_name: Optional[str]
    last_name: Optional[str]

class UserResponse(BaseModel):    # For API responses
    id: str
    email: str
    first_name: Optional[str]
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True    # Enable SQLAlchemy model conversion
```

### Custom Validators
Domain-specific validation logic:

```python
from pydantic import validator
from decimal import Decimal

class ExpenseCreate(BaseModel):
    amount: Decimal
    description: str

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > Decimal('999999.99'):
            raise ValueError('Amount too large')
        return v

    @validator('description')
    def description_length(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Description cannot be empty')
        return v.strip()
```

## Testing Architecture

### Test Organization
Tests mirror the domain structure:

```
tests/
├── conftest.py              # Global test fixtures
├── test_auth/               # Authentication tests
│   ├── test_service.py      # Business logic tests
│   ├── test_router.py       # API endpoint tests
│   └── test_models.py       # Database model tests
├── test_cycles/
└── utils.py                 # Test utilities
```

### Test Database
Isolated test database for each test session:

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

# Test database
TEST_DATABASE_URL = "postgresql://test_user:test_pass@localhost/test_colony"
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(test_db):
    """Provide database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    """FastAPI test client with database override."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Test Patterns
Consistent testing approaches:

```python
# tests/test_auth/test_service.py
import pytest
from app.auth import service
from app.auth.exceptions import UserAlreadyExistsException

class TestAuthService:
    def test_create_user_success(self, db_session):
        """Test successful user creation."""
        user_data = {
            "email": "test@example.com",
            "password": "securepass123"
        }

        user = service.create_user(db_session, user_data)

        assert user.email == "test@example.com"
        assert user.active is True
        assert user.id is not None

    def test_create_user_duplicate_email(self, db_session):
        """Test duplicate email handling."""
        user_data = {
            "email": "test@example.com",
            "password": "securepass123"
        }

        # Create first user
        service.create_user(db_session, user_data)

        # Attempt to create duplicate
        with pytest.raises(UserAlreadyExistsException):
            service.create_user(db_session, user_data)
```

## Configuration Management

### Environment-based Config
Secure configuration using Pydantic settings:

```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Colony API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["*"]

    # External APIs
    EXCHANGE_RATE_API_KEY: str
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate-api.com/v4/latest"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Environment Files
Development and production configurations:

```bash
# .env.development
DATABASE_URL=postgresql://colony_user:colony_pass@localhost:5432/colony_dev
SECRET_KEY=development-secret-key
DEBUG=true
LOG_LEVEL=DEBUG

# .env.production
DATABASE_URL=postgresql://user:pass@prod-db:5432/colony_prod
SECRET_KEY=${COLONY_SECRET_KEY}
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_HOSTS=["api.colony.app"]
```

## Logging & Monitoring

### Structured Logging
Consistent logging across all domains:

```python
# app/logging.py
import logging
import json
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Usage in services
logger = logging.getLogger(__name__)

async def create_user(db: Session, user_data: dict):
    logger.info("Creating new user", extra={"email": user_data["email"]})
    try:
        # ... business logic
        logger.info("User created successfully", extra={"user_id": str(user.id)})
        return user
    except Exception as e:
        logger.error("Failed to create user", extra={"error": str(e)})
        raise
```

## Performance Considerations

### Database Query Optimization
- Use `select_related()` for foreign key relationships
- Implement pagination for large datasets
- Add database indexes for frequently queried fields
- Use database-level constraints for data integrity

### Caching Strategy
- Redis for session data and frequently accessed lookups
- Application-level caching for exchange rates
- Query result caching for expensive reports

### Async Operations
- Use `async`/`await` for I/O operations
- Background tasks for non-critical operations (emails, reports)
- Connection pooling for database and external API calls

This architecture provides a robust foundation for building a maintainable, scalable, and secure expense management API while following FastAPI and Python best practices.
