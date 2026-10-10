from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def isolated_activities(monkeypatch):
    test_activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", test_activities)
    return test_activities


@pytest.fixture
def client(isolated_activities):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant_and_is_visible_in_activities(client):
    email = "student@mergington.edu"

    response = client.post(
        "/activities/Soccer%20Team/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Soccer Team"
    }
    assert email in activities_response.json()["Soccer Team"]["participants"]


def test_signup_rejects_duplicate_participant_without_changing_activity(client):
    email = "michael@mergington.edu"

    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities_response.json()["Chess Club"]["participants"].count(email) == 1


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = "michael@mergington.edu"

    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }
    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unregistered_participant(client):
    email = "student@mergington.edu"

    response = client.delete(
        "/activities/Soccer%20Team/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities_response.json()["Soccer Team"]["participants"] == []


def test_signup_requires_email_query_parameter(client):
    response = client.post("/activities/Soccer%20Team/signup")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]