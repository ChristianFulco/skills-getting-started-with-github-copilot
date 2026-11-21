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
