"""
Test configuration — provides a fresh in-memory database for each test.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set API key before importing app
os.environ["F2_API_KEY"] = "test-key"

from app.database import Base, get_db
from app.main import app

# Use in-memory SQLite for tests — fast, isolated, disposable
TEST_DATABASE_URL = "sqlite:///./data/test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture()
def api_key_header():
    """Auth header for write endpoints."""
    return {"X-API-Key": "test-key"}
