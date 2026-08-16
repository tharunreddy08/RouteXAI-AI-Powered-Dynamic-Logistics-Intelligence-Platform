import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Must be set before any `app.*` module is imported anywhere in the test
# session — app.config.get_settings() and app.database's engine are created
# once at first import and cached, so setting DATABASE_URL later has no
# effect and different test files would silently share (or fight over) the
# same connection.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_routexai_suite.db")
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest

from app.database import Base, engine


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    db_path = "test_routexai_suite.db"
    if os.path.exists(db_path):
        os.remove(db_path)
