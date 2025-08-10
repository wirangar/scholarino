import pytest
import os
import json
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from smartstudentbot.utils.db_utils import Base, engine
from smartstudentbot.models import User

@pytest.fixture(scope="function")
def db_session():
    """
    Pytest fixture to set up and tear down the database for each test function.
    This creates all tables before the test and drops them afterwards,
    ensuring a clean slate for each test.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user() -> User:
    """
    Pytest fixture to provide a sample User object for use in tests.
    """
    return User(
        user_id=12345,
        first_name="Test",
        last_name="User",
        age=25,
        country="Italy",
        field_of_study="Computer Science",
        email="test@example.com",
        language="en",
        preferences={"notifications": True}
    )
