import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

# Use absolute imports to ensure modules are found correctly
from smartstudentbot.main import app, bot
from smartstudentbot.config import BOT_ID, WEBHOOK_SECRET

client = TestClient(app)

def test_webhook_endpoint(monkeypatch):
    """
    Tests that the webhook endpoint can receive a minimal update and responds correctly.
    This test mocks the bot's API calls to avoid real network requests.
    """
    # Mock the bot's session to prevent real API calls to Telegram
    monkeypatch.setattr(bot.session, "make_request", AsyncMock(return_value=True))

    webhook_path = f"/{BOT_ID}/{WEBHOOK_SECRET}"

    minimal_update = {
        "update_id": 10000,
        "message": {
            "message_id": 1365,
            "date": 1511189999,
            "chat": {
                "id": 1111111,
                "type": "private",
                "first_name": "Test",
                "last_name": "User",
            },
            "from": {
                "id": 1111111,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
            },
            "text": "/start",
        },
    }

    response = client.post(webhook_path, json=minimal_update)

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    assert response.json() == {"status": "ok"}, "Response JSON did not match expected"

def test_root_health_check_endpoint():
    """
    Tests the root ('/') endpoint for a health check.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "alive", "bot_id": BOT_ID}
