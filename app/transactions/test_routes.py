import pytest
from starlette.status import HTTP_200_OK, HTTP_201_CREATED
from starlette.testclient import TestClient

from app.auth.models import AuthUser
from app.transactions.models import TransactionRead


@pytest.fixture
def init_accounts(client: TestClient, auth_user: AuthUser, account: dict):
    client.put('/accounts/1', json=account)
    account['name'] += '2'
    client.put('/accounts/2', json=account)
    yield


def assert_transaction(actual, expected):
    assert actual['name'] == expected['name']

    assert len(actual['debits']) == len(expected['debits'])
    for x, y in zip(actual['debits'], expected['debits']):
        assert x['amount'] == y['amount']
        assert x['date'] == y['date']
        assert x.get('accountUserId', None) == y.get('accountUserId', None)

    assert len(actual['credits']) == len(expected['credits'])
    for x, y in zip(actual['credits'], expected['credits']):
        assert x['amount'] == y['amount']
        assert x['date'] == y['date']
        assert x.get('accountUserId', None) == y.get('accountUserId', None)

    if 'amount' in expected:
        assert actual['amount'] == expected['amount']
    assert actual['amount'] == sum(x['amount'] for x in actual['credits'])

    if 'date' in expected:
        assert actual['date'] == expected['date']
    assert actual['date'] == min(x['date'] for x in actual['debits'] + actual['credits'])

    TransactionRead.model_validate(actual)


class TestGetAll:
    def test_get_all_empty(self, client: TestClient, auth_user: AuthUser):
        response = client.get('/transactions')
        data = response.json()
        assert response.status_code == HTTP_200_OK
        assert data == []

    def test_get_all_not_empty(self, client: TestClient, auth_user: AuthUser, init_accounts, transaction):
        client.post('/transactions', json=transaction)
        response = client.get('/transactions')
        data = response.json()
        assert response.status_code == HTTP_200_OK
        assert len(data) == 1
        assert_transaction(data[0], transaction)


class TestCreate:
    def test_create_with_no_account_user(self, client: TestClient, auth_user: AuthUser, transaction):
        response = client.post('/transactions', json=transaction)
        data = response.json()
        assert response.status_code == HTTP_201_CREATED
        assert response.headers['Location'] == f'/transactions/{data['id']}'
        assert_transaction(data, transaction)

    def test_create_with_nonexistent_account_user(self, client: TestClient, auth_user: AuthUser, transaction):
        transaction['debits'][0]['accountUserId'] = 'random'
        transaction['credits'][0]['accountUserId'] = 'crazy'
        response = client.post('/transactions', json=transaction)
        data = response.json()

        assert response.status_code == HTTP_201_CREATED
        assert response.headers['Location'] == f'/transactions/{data['id']}'
        transaction['debits'][0]['accountUserId'] = None
        transaction['credits'][0]['accountUserId'] = None
        assert_transaction(data, transaction)

    def test_create_with_existing_account_user(
            self,
            client: TestClient,
            auth_user: AuthUser,
            init_accounts,
            transaction
    ):
        response = client.get('/accounts')
        data = response.json()

        transaction['debits'][0]['accountUserId'] = data[0]['users'][0]['id']
        transaction['credits'][0]['accountUserId'] = data[1]['users'][0]['id']
        response = client.post('/transactions', json=transaction)
        data = response.json()

        assert response.status_code == HTTP_201_CREATED
        assert response.headers['Location'] == f'/transactions/{data['id']}'
        assert_transaction(data, transaction)


class TestUpdate:
    def test_update_update_entry_amounts(self, client: TestClient, auth_user: AuthUser, transaction):
        response = client.post('/transactions', json=transaction)
        data = response.json()
        data['debits'][0]['amount'] = 200
        data['credits'][0]['amount'] = 200
        del data['id']
        del data['date']
        del data['amount']
        response = client.put(response.headers['Location'], json=data)
        data2 = response.json()

        assert response.status_code == HTTP_200_OK
        assert_transaction(data2, data)

    def test_update_add_entry(self, client: TestClient, auth_user: AuthUser, transaction):
        response = client.post('/transactions', json=transaction)
        data = response.json()
        data['debits'][0]['amount'] *= 2
        data['credits'].append({'amount': data['credits'][0]['amount'], 'date': data['credits'][0]['date']})
        del data['id']
        del data['date']
        del data['amount']
        response = client.put(response.headers['Location'], json=data)
        data2 = response.json()

        assert response.status_code == HTTP_200_OK
        assert_transaction(data2, data)

    def test_update_change_entry_account_user(self, client: TestClient, auth_user: AuthUser, transaction, init_accounts):
        response = client.get('/accounts')
        accounts = response.json()
        response = client.post('/transactions', json=transaction)
        data = response.json()
        data['credits'][0]['accountUserId'] = accounts[0]['users'][0]['id']
        del data['id']
        del data['date']
        del data['amount']
        response = client.put(response.headers['Location'], json=data)
        data2 = response.json()

        assert response.status_code == HTTP_200_OK
        assert_transaction(data2, data)
