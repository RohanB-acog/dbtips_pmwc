from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Fetch database connection details from environment variables
POSTGRES_USER: str = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB: str = os.getenv("POSTGRES_DB")
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")

# Define the PostgreSQL database URL using environment variables
SQLALCHEMY_DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"

# Create the engine and session for the PostgreSQL database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for model definitions
Base = declarative_base()


# Dependency to provide a session to the routes
def get_db():
    """
    Dependency that provides a database session to be used in the FastAPI routes.
    It ensures that the session is closed after the route is processed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
