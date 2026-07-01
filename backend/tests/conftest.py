import os
import uuid as _uuid

# Must be set before any import that triggers config.py (e.g. scrapers/github.py)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ANTHROPIC_API_KEY", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CLERK_SECRET_KEY", "test")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "test")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test")
os.environ.setdefault("TWILIO_FROM_NUMBER", "+10000000000")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID
from base import Base

# Teach SQLite to treat postgres UUID columns as CHAR(36)
UUID.__visit_name__ = "uuid"


@pytest.fixture(scope="session")
def engine():
    from sqlalchemy.dialects.sqlite import base as sqlite_base
    sqlite_base.SQLiteTypeCompiler.visit_uuid = lambda self, type_, **kw: "CHAR(36)"

    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import models  # noqa: F401 — registers all ORM models on Base.metadata
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def auth_client_id():
    """Returns the UUID injected by get_authenticated_client. Override per test file."""
    return _uuid.uuid4()


@pytest.fixture
def api_client(db, auth_client_id):
    from fastapi.testclient import TestClient
    from main import app
    from database import get_db
    from auth.clerk import get_authenticated_client

    def _override_get_db():
        yield db

    def _override_auth():
        return auth_client_id

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_authenticated_client] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_api_client(db):
    """Factory: creates a TestClient authenticated as any given client_id."""
    from fastapi.testclient import TestClient
    from main import app
    from database import get_db
    from auth.clerk import get_authenticated_client

    def _factory(client_id):
        def _override_get_db():
            yield db

        def _override_auth():
            return client_id

        app.dependency_overrides[get_db] = _override_get_db
        app.dependency_overrides[get_authenticated_client] = _override_auth
        return TestClient(app)

    yield _factory
    app.dependency_overrides.clear()
