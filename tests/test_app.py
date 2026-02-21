import copy

test_data_backup = None


def setup_module(module):
    """Save a pristine copy of the activity database before any tests run."""
    from src import app as api

    global test_data_backup
    test_data_backup = copy.deepcopy(api.activities)


def teardown_function(function):
    """Restore the activity database after each test (AAA: Arrange)."""
    from src import app as api

    api.activities = copy.deepcopy(test_data_backup)


from fastapi.testclient import TestClient

from src import app as api

# create a client once; state is reset between tests by teardown_function
client = TestClient(api)


def test_get_activities_returns_initial_data():
    # Arrange: teardown_function already reset the database
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["max_participants"] == 12


def test_signup_adds_participant():
    # Arrange
    email = "tester@school.edu"
    activity = "Chess Club"

    # Act
    resp = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Signed up")
    assert email in api.activities[activity]["participants"]


def test_signup_nonexistent_activity_returns_404():
    # Arrange
    email = "foo@bar"
    # Act
    resp = client.post("/activities/NoSuchClub/signup?email=" + email)
    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_unregister_removes_participant():
    # Arrange: make sure a participant is present
    activity = "Chess Club"
    email = "somebody@school.edu"
    api.activities[activity]["participants"].append(email)

    # Act
    resp = client.delete(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Removed")
    assert email not in api.activities[activity]["participants"]


def test_unregister_nonexistent_activity_returns_404():
    # Act
    resp = client.delete("/activities/NoClub/signup?email=x@x")
    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up_returns_404():
    # Arrange
    activity = "Chess Club"
    email = "ghost@school.edu"
    # Ensure email is not in list
    if email in api.activities[activity]["participants"]:
        api.activities[activity]["participants"].remove(email)

    # Act
    resp = client.delete(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Student not signed up"
