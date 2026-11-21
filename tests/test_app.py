from copy import deepcopy

from fastapi.testclient import TestClient
import pytest

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


client = TestClient(app)


def test_root_redirects_to_static_page():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()

    chess_club = response.json()["Chess Club"]
    assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
    assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert chess_club["max_participants"] == 12
    assert chess_club["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_preserves_existing_and_adds_six_activities():
    assert {"Chess Club", "Programming Class", "Gym Class"} <= activities.keys()
    assert {
        "Soccer Team",
        "Basketball Team",
        "Art Club",
        "Drama Club",
        "Math Club",
        "Debate Team",
    } <= activities.keys()


def test_signup_adds_participant():
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Soccer%20Team/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email in activities["Soccer Team"]["participants"]
    assert response.json()["message"] == (
        "Signed up new.student@mergington.edu for Soccer Team"
    )


def test_duplicate_signup_is_rejected():
    email = "duplicate@mergington.edu"

    first = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )
    duplicate = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    assert first.status_code == 200
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Student is already signed up"
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant():
    email = "michael@mergington.edu"

    response = client.request(
        "DELETE",
        "/activities/Chess%20Club/unregister",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email not in activities["Chess Club"]["participants"]
    assert response.json()["message"] == (
        "Unregistered michael@mergington.edu from Chess Club"
    )


def test_unregister_rejects_unknown_participant():
    response = client.request(
        "DELETE",
        "/activities/Chess%20Club/unregister",
        params={"email": "unknown@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up"


def test_unregister_rejects_unknown_activity():
    response = client.request(
        "DELETE",
        "/activities/Unknown%20Club/unregister",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
