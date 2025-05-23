import pytest
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT, HTTP_201_CREATED, \
    HTTP_422_UNPROCESSABLE_ENTITY
from starlette.testclient import TestClient

from app.accounts.models import AccountRead
from app.auth.models import AuthUser


@pytest.fixture
def account():
    return {
        'name': 'Chase Freedom Unlimited',
        'users': [
            {
                'name': 'John Doe',
                'mask': '0000'
            }
        ]
    }


def assert_account(actual, expected):
    assert not actual['isMerchant']
    assert actual['name'] == expected['name']

    assert len(actual['users']) == len(expected['users'])
    for a_u, e_u in zip(actual['users'], expected['users']):
        assert a_u['mask'] == e_u['mask']
        assert a_u['name'] == e_u['name']

    assert AccountRead.model_validate(actual)


class TestGetAll:
    def test_get_all_empty(self, client: TestClient, auth_user: AuthUser):
        response = client.get('/accounts')
        data = response.json()
        assert response.status_code == HTTP_200_OK
        assert data == []

    def test_get_all_not_empty(self, client: TestClient, auth_user: AuthUser, account: dict):
        client.post('/accounts', json=account)

        response = client.get('/accounts')
        data = response.json()

        assert response.status_code == HTTP_200_OK
        assert len(data) == 1

        for x in data:
            assert_account(x, account)


class TestGet:
    def test_get_nonexistent(self, client: TestClient, auth_user: AuthUser):
        response = client.get('/accounts/nonexistent')
        assert response.status_code == HTTP_404_NOT_FOUND

    def test_get_exists(self, client: TestClient, auth_user: AuthUser, account: dict):
        response = client.post('/accounts', json=account)
        data = response.json()
        id = data['id']

        response = client.get(f'/accounts/{id}')
        data = response.json()

        assert response.status_code == HTTP_200_OK
        assert_account(data, account)


class TestCreate:
    def test_create_same_account_name_in_auth_user(self, client: TestClient, auth_user: AuthUser, account: dict):
        client.post('/accounts', json=account)
        response = client.post('/accounts', json=account)
        assert response.status_code == HTTP_409_CONFLICT

    def test_create_same_mask_in_account(self, client: TestClient, auth_user: AuthUser, account: dict):
        account['users'].append(account['users'][0])
        response = client.post('/accounts', json=account)
        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_diff_mask_same_user_in_account(self, client: TestClient, auth_user: AuthUser, account: dict):
        account['users'].append({'name': account['users'][0]['name'], 'mask': account['users'][0]['mask'] + '0'})
        response = client.post('/accounts', json=account)
        data = response.json()

        assert response.status_code == HTTP_201_CREATED
        assert response.headers['Location'] == f'/accounts/{data['id']}'
        assert_account(data, account)

    def test_create_same_mask_diff_account(self, client: TestClient, auth_user: AuthUser, account: dict):
        client.post('/accounts', json=account)
        account['name'] = account['name'] + '2'
        response = client.post('/accounts', json=account)
        data = response.json()

        assert response.status_code == HTTP_201_CREATED
        assert response.headers['Location'] == f'/accounts/{data['id']}'
        assert_account(data, account)


class TestUpdate:
    def test_update_nonexistent(self, client: TestClient, auth_user: AuthUser, account: dict):
        response = client.put('/accounts/peepeepoopoo', json=account)
        data = response.json()
        assert response.status_code == HTTP_201_CREATED
        assert response.headers['Location'] == f'/accounts/peepeepoopoo'
        assert data['id'] == 'peepeepoopoo'
        assert_account(data, account)

    def test_update_add_user(self, client: TestClient, auth_user: AuthUser, account: dict):
        response = client.put('/accounts/peepoopoo', json=account)
        data = response.json()

        data['users'].append({
            'name': 'Jane Doe',
            'mask': '1111'
        })
        del data['id']

        response = client.put('/accounts/peepoopoo', json=data)
        data2 = response.json()

        assert response.status_code == HTTP_200_OK
        assert_account(data2, data)

    def test_update_add_user_same_mask(self, client: TestClient, auth_user: AuthUser, account: dict):
        response = client.put('/accounts/peepoopoo', json=account)
        data = response.json()

        data['users'].append(data['users'][0])
        del data['id']
        response = client.put('/accounts/peepoopoo', json=data)

        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_delete_user(self, client: TestClient, auth_user: AuthUser, account: dict):
        account['users'].append({
            'name': 'Jane Doe',
            'mask': '1111'
        })
        response = client.put('/accounts/peepoopoo', json=account)
        data = response.json()

        del data['users'][0]
        del data['id']

        response = client.put('/accounts/peepoopoo', json=data)
        data2 = response.json()

        assert response.status_code == HTTP_200_OK
        assert_account(data2, data)

    def test_update_update_user(self, client: TestClient, auth_user: AuthUser, account: dict):
        response = client.put('/accounts/peepoopoo', json=account)
        data = response.json()

        data['users'][0]['name'] = 'Jane Doe'
        data['users'][0]['mask'] = '1111'
        del data['id']

        response = client.put('/accounts/peepoopoo', json=data)
        data2 = response.json()

        assert response.status_code == HTTP_200_OK
        assert_account(data2, data)


class TestDelete:
    def test_delete_nonexistent(self, client: TestClient, auth_user: AuthUser, account: dict):
        response = client.delete('/accounts/nonexistent')
        assert response.status_code == HTTP_404_NOT_FOUND

    def test_delete_exists(self, client: TestClient, auth_user: AuthUser, account: dict):
        response = client.post('/accounts', json=account)
        data = response.json()

        response = client.delete(f'/accounts/{data['id']}')
        assert response.status_code == HTTP_200_OK
