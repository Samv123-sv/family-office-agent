from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from base import Base  # noqa: F401 — re-exported for convenience

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
