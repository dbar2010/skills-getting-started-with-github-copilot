import pytest

from src import app as app_module


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_records(client):
    # Arrange
    expected_activities = app_module.activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities
    assert all(
        {"description", "schedule", "max_participants", "participants"} <= activity.keys()
        for activity in response.json().values()
    )


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = app_module.activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_unregisters_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = app_module.activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_detail"),
    [
        ("Unknown Club", "student@mergington.edu", "Activity not found"),
        ("Chess Club", "not.signed.up@mergington.edu", "Student is not signed up for this activity"),
    ],
)
def test_remove_participant_returns_not_found_for_invalid_request(
    client, activity_name, email, expected_detail
):
    # Arrange
    path = f"/activities/{activity_name}/signup"

    # Act
    response = client.delete(path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/activities/Chess Club/signup"),
        ("delete", "/activities/Chess Club/signup"),
    ],
)
def test_signup_and_remove_require_email_query_parameter(client, method, path):
    # Arrange
    request = getattr(client, method)

    # Act
    response = request(path)

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]