from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
from .logging import logger as log


# Build PostgreSQL connection URL
DATABASE_URL = f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5
)

# Create declarative base
DataBase = declarative_base()

# Create session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_database():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_connected() -> bool:
    """Check if database is connected"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        log.info("PostgreSQL connection successful")
        return True
    except Exception as e:
        log.error(f"PostgreSQL connection failed: {e}")
        return False
