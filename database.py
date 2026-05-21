from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite database file will be created at project root
DATABASE_URL = "sqlite:///./techworld.db"

# Create the SQLAlchemy engine
# connect_args is required for SQLite to allow multi-threaded access (FastAPI uses threads)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Each instance of SessionLocal is a database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# All models inherit from this Base
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a request-scoped DB session,
    then closes it automatically when the request is done.

    Usage in a controller:
        from database import get_db
        from fastapi import Depends
        from sqlalchemy.orm import Session

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables defined in models.
    Called once at app startup (from main.py lifespan).
    """
    # Import models here so Base knows about them before create_all()
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def migrate_schema():
    """Apply small SQLite schema updates that create_all() cannot add."""
    with engine.begin() as conn:
        order_columns = {
            row[1]
            for row in conn.exec_driver_sql("PRAGMA table_info(orders)").fetchall()
        }
        if "recipient_name" not in order_columns:
            conn.exec_driver_sql("ALTER TABLE orders ADD COLUMN recipient_name VARCHAR")
