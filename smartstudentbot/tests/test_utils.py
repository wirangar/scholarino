import pytest
import os
import json
import sys

# Add project root to the path to allow imports from smartstudentbot
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, os.path.dirname(project_root))

from unittest.mock import patch, AsyncMock
from smartstudentbot.utils.db_utils import save_news, save_user, get_user, add_points_to_user, get_leaderboard
from unittest.mock import patch, AsyncMock
from smartstudentbot.utils.db_utils import save_news, save_user, get_user, add_points_to_user, get_leaderboard, find_matching_roommates
from smartstudentbot.utils.gamification import award_points_for_action
from smartstudentbot.models import User, RoommatePreferences

NEWS_JSON_PATH = "smartstudentbot/news.json"

@pytest.mark.asyncio
async def test_save_news_in_memory(db_session):
    """
    Tests that the save_news function correctly writes news
    to the in-memory DB and the backup JSON file.
    """
    # Create a dummy news.json for testing
    with open(NEWS_JSON_PATH, "w") as f:
        json.dump({"version": "1.0", "data": []}, f)

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

    # Teardown
    if os.path.exists(NEWS_JSON_PATH):
         with open(NEWS_JSON_PATH, "w") as f:
            json.dump({"version": "1.0", "data": []}, f)

@pytest.mark.asyncio
async def test_save_and_get_user(db_session, sample_user):
    """
    Tests creating, retrieving, and verifying a user.
    """
    # 1. Save the user
    await save_user(sample_user)

    # 2. Get the user back from the DB
    retrieved_user = await get_user(sample_user.user_id)

    # 3. Assert the retrieved user matches the original
    assert retrieved_user is not None
    assert retrieved_user.user_id == sample_user.user_id
    assert retrieved_user.first_name == sample_user.first_name
    assert retrieved_user.email == sample_user.email
    assert retrieved_user.preferences == sample_user.preferences

@pytest.mark.asyncio
async def test_update_user(db_session, sample_user):
    """
    Tests that saving a user with an existing ID updates the record.
    """
    # 1. Save the initial user
    await save_user(sample_user)

    # 2. Modify the user object and save again
    sample_user.first_name = "Updated"
    sample_user.country = "Germany"
    await save_user(sample_user)

    # 3. Retrieve the user and check if the fields are updated
    updated_user = await get_user(sample_user.user_id)
    assert updated_user.first_name == "Updated"
    assert updated_user.country == "Germany"

@pytest.mark.asyncio
async def test_get_nonexistent_user(db_session):
    """
    Tests that get_user returns None for a user that does not exist.
    """
    retrieved_user = await get_user(99999)
    assert retrieved_user is None

@pytest.mark.asyncio
async def test_add_points(db_session, sample_user):
    """
    Tests adding points to a user.
    """
    await save_user(sample_user)
    await add_points_to_user(sample_user.user_id, 50)
    updated_user = await get_user(sample_user.user_id)
    assert updated_user.points == 50
    await add_points_to_user(sample_user.user_id, 25)
    updated_user_2 = await get_user(sample_user.user_id)
    assert updated_user_2.points == 75

@pytest.mark.asyncio
async def test_get_leaderboard(db_session, sample_user):
    """
    Tests retrieving the leaderboard.
    """
    # Create another user
    user2 = sample_user.model_copy(update={"user_id": 54321, "first_name": "Jane"})
    await save_user(sample_user) # 0 points
    await save_user(user2) # 0 points

    await add_points_to_user(sample_user.user_id, 100)
    await add_points_to_user(user2.user_id, 150)

    leaderboard = await get_leaderboard(limit=5)
    assert len(leaderboard) == 2
    assert leaderboard[0].user_id == user2.user_id # Jane should be first
    assert leaderboard[0].points == 150
    assert leaderboard[1].user_id == sample_user.user_id
    assert leaderboard[1].points == 100

@pytest.mark.asyncio
@patch("smartstudentbot.utils.gamification.add_points_to_user", new_callable=AsyncMock)
async def test_award_points_for_action(mock_add_points, db_session, sample_user):
    """
    Tests the central gamification logic for awarding points.
    """
    await award_points_for_action(sample_user.user_id, "complete_registration")
    mock_add_points.assert_called_once_with(sample_user.user_id, 25)

@pytest.mark.asyncio
async def test_find_matching_roommates(db_session, sample_user):
    """
    Tests the roommate matching logic.
    """
    # User 1 (the searcher)
    sample_user.roommate_prefs = RoommatePreferences(looking_for_roommate=True, budget_max=300, smoker=False)
    await save_user(sample_user)

    # User 2 (a good match)
    user2 = sample_user.model_copy(update={"user_id": 54321, "first_name": "Jane"})
    user2.roommate_prefs = RoommatePreferences(looking_for_roommate=True, budget_max=300, smoker=False)
    await save_user(user2)

    # User 3 (not looking)
    user3 = sample_user.model_copy(update={"user_id": 67890, "first_name": "Mike"})
    user3.roommate_prefs = RoommatePreferences(looking_for_roommate=False)
    await save_user(user3)

    matches = await find_matching_roommates(sample_user)
    assert len(matches) == 1
    assert matches[0].user_id == user2.user_id
