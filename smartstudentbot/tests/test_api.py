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

# --- Admin Dashboard Tests ---

def test_admin_login_page_loads():
    """Tests that the admin login page loads correctly."""
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "Admin Panel Login" in response.text

def test_admin_login_fail_wrong_password():
    """Tests that login fails with an incorrect password."""
    response = client.post("/admin/login", data={"password": "wrongpassword"})
    assert response.status_code == 200 # It returns the login page again
    assert "Invalid password" in response.text

def test_admin_dashboard_redirects_if_not_logged_in():
    """Tests that the dashboard redirects to login if no session cookie is present."""
    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 307 # Temporary Redirect
    assert response.headers["location"] == "http://testserver/admin/login"

def test_admin_login_success_and_dashboard_access():
    """Tests a full successful login flow and dashboard access."""
    # 1. Login successfully
    response_login = client.post("/admin/login", data={"password": "strongpassword123"}, follow_redirects=False)
    assert response_login.status_code == 302 # Found - redirecting
    assert response_login.headers["location"] == "http://testserver/admin/dashboard"

    # 2. Use the session cookie from the successful login to access the dashboard
    session_cookie = response_login.cookies.get("admin_session")
    assert session_cookie is not None

    response_dashboard = client.get("/admin/dashboard", cookies={"admin_session": session_cookie})
    assert response_dashboard.status_code == 200
    assert "Admin Dashboard" in response_dashboard.text
    assert "Registered Users" in response_dashboard.text
