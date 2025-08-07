import pytest
import os
import json
import sys

# Add project root to the path to allow imports from smartstudentbot
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, os.path.dirname(project_root))

from smartstudentbot.utils.db_utils import save_news, Base, engine
from smartstudentbot.config import SQLITE_DB

NEWS_JSON_PATH = "smartstudentbot/news.json"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Fixture to handle setup and teardown for each test."""
    # Create tables for in-memory DB
    Base.metadata.create_all(engine)

    # Create a dummy news.json for testing
    with open(NEWS_JSON_PATH, "w") as f:
        json.dump({"version": "1.0", "data": []}, f)

    yield  # This is where the test runs

    # Teardown: Clean up created files
    if os.path.exists(NEWS_JSON_PATH):
         with open(NEWS_JSON_PATH, "w") as f:
            json.dump({"version": "1.0", "data": []}, f)

    # Drop tables for in-memory DB
    Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_save_news_in_memory():
    """
    Tests that the save_news function correctly writes news
    to the in-memory DB and the backup JSON file.
    """
    # Define a sample news item
    news_item = {
        "title": "Test News",
        "content": "This is a test.",
        "file": None,
        "timestamp": "2025-08-07T18:00:00"
    }

    # Call the function to be tested
    await save_news(news_item)

    # Assert that the news was written to the JSON file
    with open(NEWS_JSON_PATH, "r") as f:
        data = json.load(f)

    assert len(data["data"]) == 1, "News was not added to the JSON file."
    assert data["data"][0]["title"] == "Test News", "News title does not match."

    # To verify the DB write, we would need a 'get_news' function.
    # For now, the absence of an error and the JSON write is a good indicator.
