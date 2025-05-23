from fastapi.testclient import TestClient

from app.auth.models import AuthUser


def test_whoami(client: TestClient, auth_user: AuthUser):
    response = client.get('/whoami')
    data = response.json()
    assert response.status_code == 200
    assert data['id'] == auth_user.id
