import pytest
from fastapi.testclient import TestClient

from ai_for_science.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.integration
def test_api_overview():
    response = client.get("/api/overview")
    assert response.status_code == 200


@pytest.mark.integration
def test_api_dimensions():
    response = client.get("/api/dimensions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.integration
def test_api_comparisons():
    response = client.get("/api/comparisons")
    assert response.status_code == 200


@pytest.mark.integration
def test_api_references():
    response = client.get("/api/references")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.integration
def test_api_unknown_dimension():
    response = client.get("/api/comparisons/nonexistent")
    assert response.status_code == 404
