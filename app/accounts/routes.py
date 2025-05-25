from fastapi import APIRouter, Response
from starlette.status import HTTP_201_CREATED

from app.accounts.balance.models import AccountBalanceRead
from app.accounts.balance.services import get_account_balance
from app.accounts.models import AccountRead, AccountCreate, AccountUpdate
from app.accounts.services import get_all_accounts, get_account_by_id, create_account, delete_account, \
    upsert_account
from app.deps import DBSessionDep, AuthUserDep

router = APIRouter(
    prefix='/accounts',
    tags=['accounts']
)


@router.get('/')
async def get_all(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        include_merchants: bool = False,
) -> list[AccountRead]:
    """Returns all accounts from `auth_user`."""
    return get_all_accounts(db, auth_user, include_merchants)


@router.get('/{id}')
async def get(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str,
        include_merchants: bool = False,
) -> AccountRead:
    """Returns account with `id` from `auth_user`."""
    return get_account_by_id(db, auth_user, id, include_merchants)


@router.post('/', status_code=HTTP_201_CREATED)
async def create(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        body: AccountCreate,
        response: Response,
) -> AccountRead:
    """Creates a new account for `auth_user`."""
    data = create_account(db, auth_user, body)
    response.headers['Location'] = f'{router.prefix}/{data.id}'
    return data


@router.put('/{id}')
async def upsert(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str,
        body: AccountUpdate,
        response: Response,
) -> AccountRead:
    """Upserts `body` to account with `id` for `auth_user`."""
    data, is_created = upsert_account(db, auth_user, id, body)

    if not is_created:
        return data

    response.status_code = HTTP_201_CREATED
    response.headers['Location'] = f'{router.prefix}/{data.id}'
    return data


@router.delete('/{id}')
async def delete(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str,
):
    """Deletes account with `id` from `auth_user`."""
    delete_account(db, auth_user, id)


@router.get('/{id}/balance')
async def get_balances(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str,
) -> AccountBalanceRead:
    """Returns account with `id` including its balance series from `auth_user`."""
    return get_account_balance(db, auth_user, id)
