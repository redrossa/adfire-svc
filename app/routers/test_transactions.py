from nanoid import generate
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from starlette.testclient import TestClient

from app.models.auth import AuthUser
from app.models.transactions import Transaction

transaction = {
    'name': 'Grocery',
    'date': '2025-06-06',
    'amount': '46.92',
    'isCredit': False,
    'account': 'Amex Gold'
}


def assert_transaction(actual, expected):
    assert actual['name'] == expected['name']
    assert actual['date'] == expected['date']
    assert actual['amount'] == expected['amount']
    assert actual['isCredit'] == expected['isCredit']
    assert actual['account'] == expected['account']

    Transaction.model_validate(actual)


class TestGetAll:
    def test_get_all_empty(self, client: TestClient, auth_user: AuthUser):
        response = client.get('/transactions')
        data = response.json()
        assert response.status_code == HTTP_200_OK
        assert data == []

    def test_get_all_not_empty(self, client: TestClient, auth_user: AuthUser):
        client.post('/transactions', json=transaction)
        response = client.get('/transactions')
        data = response.json()
        assert response.status_code == HTTP_200_OK
        assert len(data) == 1
        assert_transaction(data[0], transaction)


class TestCreate:
    def test_create(self, client: TestClient, auth_user: AuthUser):
        response = client.post('/transactions', json=transaction)
        data = response.json()
        assert response.status_code == HTTP_201_CREATED
        assert response.headers['Location'] == f'/transactions/{data['id']}'
        assert_transaction(data, transaction)


class TestUpdate:
    def test_update_non_existing_id(self, client: TestClient, auth_user: AuthUser):
        id = generate()
        response = client.put(f'/transactions/{id}', json=transaction)
        data = response.json()
        assert response.status_code == HTTP_201_CREATED
        assert response.headers['Location'] == f'/transactions/{data['id']}'
        assert_transaction(data, transaction)

    def test_update_existing_id(self, client: TestClient, auth_user: AuthUser):
        id = generate()
        response = client.put(f'/transactions/{id}', json=transaction)
        data = response.json()
        data['name'] = 'Not Grocery'
        del data['id']
        response = client.put(f'/transactions/{id}', json=data)
        data2 = response.json()
        assert_transaction(data2, data)


class TestDelete:
    def test_delete(self, client: TestClient, auth_user: AuthUser):
        response = client.post('/transactions', json=transaction)
        data = response.json()
        response = client.delete(f'/transactions/{data["id"]}')
        assert response.status_code == HTTP_200_OK

    def test_delete_not_exists(self, client: TestClient, auth_user: AuthUser):
        id = generate()
        response = client.delete(f'/transactions/{id}')
        assert response.status_code == HTTP_404_NOT_FOUND
