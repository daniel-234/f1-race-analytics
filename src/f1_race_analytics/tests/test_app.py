import pytest
from fastapi.testclient import TestClient

from f1_race_analytics.app import app
from f1_race_analytics.database import create_races, get_session


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_replay_404_when_url_unset(client, monkeypatch):
    monkeypatch.setattr("f1_race_analytics.app.REPLAY_URL", None)

    response = client.get("/replay")

    assert response.status_code == 404


def test_index_lists_races(client, session, race_events):
    create_races(session, 2026, race_events)

    response = client.get("/")

    assert response.status_code == 200
    assert "Melbourne" in response.text


def test_drivers_standings(client, seeded_season):
    response = client.get("/standings/drivers")

    assert response.status_code == 200
    body = response.text
    order = ["Antonelli", "Russell", "Leclerc", "Hamilton"]
    positions = [body.index(name) for name in order]
    assert positions == sorted(positions)


def test_constructors_standings(client, seeded_season):
    response = client.get("/standings/constructors")

    assert response.status_code == 200
    body = response.text
    order = ["Mercedes", "Ferrari"]
    positions = [body.index(name) for name in order]
    assert positions == sorted(positions)


def test_race_results(client, seeded_season):
    response = client.get("/results/albert_park")

    assert response.status_code == 200
    assert "Russell" in response.text
