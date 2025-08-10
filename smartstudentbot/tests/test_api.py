import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

# Use absolute imports
from smartstudentbot.main import app, bot
from smartstudentbot.config import BOT_ID, WEBHOOK_SECRET

client = TestClient(app)

def test_webhook_endpoint(monkeypatch):
    monkeypatch.setattr(bot.session, "make_request", AsyncMock(return_value=True))
    webhook_path = f"/{BOT_ID}/{WEBHOOK_SECRET}"
    minimal_update = {"update_id": 1}
    response = client.post(webhook_path, json=minimal_update)
    assert response.status_code == 200

def test_root_health_check_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
