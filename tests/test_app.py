from fastapi.testclient import TestClient

from backend_posts_api.app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
