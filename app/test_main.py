from fastapi.testclient import TestClient

from app.models import auth


def test_whoami(client: TestClient, auth_user: auth.AuthUser):
    response = client.get('/whoami')
    data = response.json()
    assert response.status_code == 200
    assert data['id'] == auth_user.id
