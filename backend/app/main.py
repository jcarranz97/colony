from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.auth.models import User
from app.auth.router import router as auth_router
from app.auth.utils import get_password_hash
from app.config import settings
from app.cycles.exchange_rates_router import router as exchange_rates_router
from app.cycles.router import router as cycles_router
from app.database import Base, SessionLocal, engine
from app.exceptions import (
    AppExceptionError,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.households.models import Household, UserHouseholdMembership
from app.households.router import router as households_router
from app.payment_methods.router import router as payment_methods_router
from app.recurrent_expenses.router import router as recurrent_expenses_router
from app.recurrent_incomes.router import router as recurrent_incomes_router


def _bootstrap_admin() -> None:
    """Create the default admin user and household on first startup.

    Reads credentials from DEFAULT_ADMIN_USERNAME / DEFAULT_ADMIN_PASSWORD
    env vars (via settings.ADMIN). Safe to call on every startup — creation
    is skipped if the user already exists.
    """
    username = settings.ADMIN.USERNAME
    password = settings.ADMIN.PASSWORD

    with SessionLocal() as db:
        household = db.query(Household).filter(Household.active.is_(True)).first()
        if household is None:
            household = Household(name="Default Household")
            db.add(household)
            db.flush()

        admin = db.query(User).filter(User.username == username).first()
        if admin is None:
            admin = User(
                username=username,
                password_hash=get_password_hash(password),
                preferred_currency="USD",
                locale="en-US",
                role="admin",
            )
            db.add(admin)
            db.flush()
        elif admin.role != "admin":
            admin.role = "admin"

        has_membership = (
            db.query(UserHouseholdMembership)
            .filter(
                UserHouseholdMembership.user_id == admin.id,
                UserHouseholdMembership.household_id == household.id,
            )
            .first()
        )
        if has_membership is None:
            db.add(
                UserHouseholdMembership(
                    user_id=admin.id,
                    household_id=household.id,
                )
            )

        if admin.active_household_id is None:
            admin.active_household_id = household.id

        db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Create database tables and bootstrap the admin user on startup."""
    Base.metadata.create_all(bind=engine)
    _bootstrap_admin()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Personal expense management API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add exception handlers
    app.add_exception_handler(AppExceptionError, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValueError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(payment_methods_router, prefix="/api/v1")
    app.include_router(recurrent_expenses_router, prefix="/api/v1")
    app.include_router(recurrent_incomes_router, prefix="/api/v1")
    app.include_router(cycles_router, prefix="/api/v1")
    app.include_router(exchange_rates_router, prefix="/api/v1")
    app.include_router(households_router, prefix="/api/v1")

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint providing basic app info."""
        return {
            "message": f"{settings.APP_NAME} is running",
            "version": settings.VERSION,
            "environment": "development",
        }

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "colony-api",
            "version": settings.VERSION,
        }

    return app


app = create_app()
