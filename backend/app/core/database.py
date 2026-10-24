from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

from app.core.config import settings

# Resolve path: for sqlite, relative paths are resolved from cwd
DATABASE_URL = settings.DATABASE_URL

# create_engine args: check_same_thread=False is required for SQLite + FastAPI
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """Dependency that yields a database session with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
