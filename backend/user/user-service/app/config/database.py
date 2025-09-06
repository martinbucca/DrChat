import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://app:secret@db:5432/drchat")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5
)

DataBase = declarative_base()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
