from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    # Make a deep copy of the initial activities and restore before each test
    original = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original))


def test_get_activities():
    client = TestClient(app_module.app)
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    client = TestClient(app_module.app)
    activity = "Chess Club"
    email = "tester@example.com"

    # Ensure email not present
    res = client.get("/activities")
    participants = res.json()[activity]["participants"]
    assert email not in participants

    # Sign up
    res = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 200
    assert "Signed up" in res.json().get("message", "")

    # Now email should be present
    res = client.get("/activities")
    participants = res.json()[activity]["participants"]
    assert email in participants

    # Unregister
    res = client.post(f"/activities/{activity}/unregister", params={"email": email})
    assert res.status_code == 200
    assert "Unregistered" in res.json().get("message", "")

    # Email removed
    res = client.get("/activities")
    participants = res.json()[activity]["participants"]
    assert email not in participants


def test_signup_already_registered_returns_400():
    client = TestClient(app_module.app)
    activity = "Chess Club"
    existing = "michael@mergington.edu"
    res = client.post(f"/activities/{activity}/signup", params={"email": existing})
    assert res.status_code == 400


def test_unregister_nonexistent_returns_404():
    client = TestClient(app_module.app)
    activity = "Chess Club"
    not_registered = "noone@example.com"
    res = client.post(f"/activities/{activity}/unregister", params={"email": not_registered})
    assert res.status_code == 404
import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


def test_get_activities():
    r = client.get("/activities")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    # Basic expected activity
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "pytest_user@example.com"

    # Preserve original state and restore at the end
    original = app_module.activities[activity]["participants"].copy()
    try:
        # Ensure test email not present
        if email in original:
            pytest.skip("Test email already present in participants")

        # Signup
        r = client.post(f"/activities/{activity}/signup", params={"email": email})
        assert r.status_code == 200
        assert "Signed up" in r.json().get("message", "")

        # Verify participant appears in listing
        r = client.get("/activities")
        assert r.status_code == 200
        data = r.json()
        assert email in data[activity]["participants"]

        # Unregister
        r = client.post(f"/activities/{activity}/unregister", params={"email": email})
        assert r.status_code == 200
        assert "Unregistered" in r.json().get("message", "")

        # Verify removal
        r = client.get("/activities")
        data = r.json()
        assert email not in data[activity]["participants"]

    finally:
        # Restore original participants to avoid side effects for other tests
        app_module.activities[activity]["participants"] = original
