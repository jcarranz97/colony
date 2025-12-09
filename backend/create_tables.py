from app.database import Base, engine
from app.auth.models import User  # Import your models


def create_tables():
    """Create all tables in the database."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")


if __name__ == "__main__":
    create_tables()
