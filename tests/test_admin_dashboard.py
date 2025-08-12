import pytest
from fastapi.testclient import TestClient
import os
import json
import shutil

# This is a bit of a hack to make sure the app can be imported
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smartstudentbot.main import app
from smartstudentbot.config import ADMIN_DASHBOARD_PASSWORD
from smartstudentbot.utils.json_utils import JSON_VERSION

client = TestClient(app)

@pytest.fixture(scope="function")
def test_data_dir(tmp_path):
    """
    Pytest fixture to create a temporary data directory with empty JSON files
    for the duration of a test function. This ensures tests are isolated
    and don't interfere with real data or each other.
    """
    # Create a 'smartstudentbot' subdirectory to mimic the real structure
    source_dir = os.path.join(os.path.dirname(__file__), '../smartstudentbot')
    test_dir = tmp_path / "smartstudentbot"
    test_dir.mkdir()

    # Define paths for our test JSON files
    qna_path = test_dir / "qna.json"
    discounts_path = test_dir / "discounts.json"
    learning_path = test_dir / "italian_learning_resources.json"

    # Create empty but valid JSON files
    empty_data = {"version": JSON_VERSION, "data": []}
    with open(qna_path, "w") as f:
        json.dump(empty_data, f)
    with open(discounts_path, "w") as f:
        json.dump(empty_data, f)
    with open(learning_path, "w") as f:
        json.dump(empty_data, f)

    # Before running the test, we need to monkeypatch the file paths
    # used in the admin routes to point to our temporary files.
    from smartstudentbot.admin_web import routes
    original_paths = {
        "qna": routes.QNA_FILE_PATH,
        "discounts": routes.DISCOUNTS_FILE_PATH,
        "learning": routes.LEARNING_FILE_PATH
    }

    routes.QNA_FILE_PATH = str(qna_path)
    routes.DISCOUNTS_FILE_PATH = str(discounts_path)
    routes.LEARNING_FILE_PATH = str(learning_path)

    yield test_dir

    # Teardown: Restore original paths after the test is done
    routes.QNA_FILE_PATH = original_paths["qna"]
    routes.DISCOUNTS_FILE_PATH = original_paths["discounts"]
    routes.LEARNING_FILE_PATH = original_paths["learning"]


def test_login_and_get_dashboard(test_data_dir):
    """Test successful login and access to the dashboard."""
    # Step 1: Try to access dashboard without login, should redirect
    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 307 # Temporary Redirect

    # Step 2: Login with correct password
    login_response = client.post("/admin/login", data={"password": ADMIN_DASHBOARD_PASSWORD})
    assert login_response.status_code == 200 # OK, because it's the response from the redirect

    # The TestClient stores cookies, so subsequent requests should be authenticated
    dashboard_response = client.get("/admin/dashboard")
    assert dashboard_response.status_code == 200
    assert "Admin Dashboard" in dashboard_response.text

def test_qna_crud_flow(test_data_dir):
    """Test the full Create, Read, Update, Delete flow for the Q&A section."""
    # Login first
    client.post("/admin/login", data={"password": ADMIN_DASHBOARD_PASSWORD})

    # 1. CREATE
    response_add = client.post(
        "/admin/qna/add",
        data={"question": "Test Q", "answer": "Test A"},
        follow_redirects=False
    )
    assert response_add.status_code == 303 # See Other, redirecting after POST

    # 2. READ
    response_read = client.get("/admin/qna")
    assert response_read.status_code == 200
    assert "Test Q" in response_read.text
    assert "Test A" in response_read.text

    # Find the ID of the created item (it should be 1)
    # This is a bit fragile, a better way would be to parse the HTML
    item_id = 1

    # 3. UPDATE
    response_update = client.post(
        f"/admin/qna/edit/{item_id}",
        data={"question": "Updated Q", "answer": "Updated A"},
        follow_redirects=False
    )
    assert response_update.status_code == 303

    response_read_after_update = client.get("/admin/qna")
    assert "Updated Q" in response_read_after_update.text
    assert "Test Q" not in response_read_after_update.text

    # 4. DELETE
    response_delete = client.post(f"/admin/qna/delete/{item_id}", follow_redirects=False)
    assert response_delete.status_code == 303

    response_read_after_delete = client.get("/admin/qna")
    assert "Updated Q" not in response_read_after_delete.text
    assert "No Q&A data found" in response_read_after_delete.text

def test_discounts_crud_flow(test_data_dir):
    """Test the full Create, Read, Update, Delete flow for the Discounts section."""
    client.post("/admin/login", data={"password": ADMIN_DASHBOARD_PASSWORD})

    # 1. CREATE
    client.post(
        "/admin/discounts/add",
        data={"store": "Test Store", "offer": "10% off", "conditions": "Students only"},
        follow_redirects=False
    )

    # 2. READ
    response_read = client.get("/admin/discounts")
    assert response_read.status_code == 200
    assert "Test Store" in response_read.text

    item_id = 1

    # 3. UPDATE
    client.post(
        f"/admin/discounts/edit/{item_id}",
        data={"store": "Updated Store", "offer": "20% off", "conditions": "All students"},
        follow_redirects=False
    )

    response_read_after_update = client.get("/admin/discounts")
    assert "Updated Store" in response_read_after_update.text
    assert "Test Store" not in response_read_after_update.text

    # 4. DELETE
    client.post(f"/admin/discounts/delete/{item_id}", follow_redirects=False)

    response_read_after_delete = client.get("/admin/discounts")
    assert "Updated Store" not in response_read_after_delete.text
    assert "No discount data found" in response_read_after_delete.text

def test_learning_crud_flow(test_data_dir):
    """Test the full Create, Read, Update, Delete flow for the Learning Resources section."""
    client.post("/admin/login", data={"password": ADMIN_DASHBOARD_PASSWORD})

    # 1. CREATE
    client.post(
        "/admin/learning/add",
        data={"type": "Website", "name": "Test Site", "description": "A site for testing", "link": "http://example.com"},
        follow_redirects=False
    )

    # 2. READ
    response_read = client.get("/admin/learning")
    assert response_read.status_code == 200
    assert "Test Site" in response_read.text

    item_id = 1

    # 3. UPDATE
    client.post(
        f"/admin/learning/edit/{item_id}",
        data={"type": "Book", "name": "Updated Book", "description": "An updated book", "link": "http://example.com/book"},
        follow_redirects=False
    )

    response_read_after_update = client.get("/admin/learning")
    assert "Updated Book" in response_read_after_update.text
    assert "Test Site" not in response_read_after_update.text

    # 4. DELETE
    client.post(f"/admin/learning/delete/{item_id}", follow_redirects=False)

    response_read_after_delete = client.get("/admin/learning")
    assert "Updated Book" not in response_read_after_delete.text
    assert "No learning resources found" in response_read_after_delete.text
