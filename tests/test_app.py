from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from backend_posts_api.app import _verify_jwt, app
from backend_posts_api.database import get_session

client = TestClient(app)


async def override_verify_jwt(token):
    return None


async def override_get_session():
    all_mock = MagicMock()
    all_mock.all = MagicMock()
    all_mock.all.return_value = []
    mock = AsyncMock()
    mock.exec = AsyncMock()
    mock.exec.return_value = all_mock
    return mock


app.dependency_overrides[_verify_jwt] = override_verify_jwt
app.dependency_overrides[get_session] = override_get_session


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_list_all_users():
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json() == []
