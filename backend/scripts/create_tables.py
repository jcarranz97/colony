import app.auth.models
import app.cycles.models
import app.payment_methods.models
import app.recurrent_expenses.models
import app.recurrent_incomes.models  # noqa: F401
from app.database import Base, engine


def create_tables() -> None:
    """Create all tables in the database."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")


if __name__ == "__main__":
    create_tables()
