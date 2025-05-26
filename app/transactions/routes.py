from fastapi import APIRouter, Response
from fastapi.params import Query
from starlette.status import HTTP_201_CREATED

from app.deps import DBSessionDep, AuthUserDep
from app.transactions.models import TransactionRead, TransactionCreate, TransactionUpdate
from app.transactions.services import get_all_transactions, get_transaction_by_id, create_transaction, \
    upsert_transaction, delete_transaction, get_transactions_by_account_id

router = APIRouter(
    prefix='/transactions',
    tags=['transactions']
)


@router.get('/')
async def get_all(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        account_id: str | None = Query(None, alias='accountId'),
) -> list[TransactionRead]:
    """Returns all transactions from `auth_user`."""
    if account_id:
        return get_transactions_by_account_id(db, auth_user, account_id)

    return get_all_transactions(db, auth_user)


@router.get('/{id}')
async def get(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str
) -> TransactionRead:
    """Returns transaction with `id` from `auth_user`."""
    return get_transaction_by_id(db, auth_user, id)


@router.post('/', status_code=HTTP_201_CREATED)
async def create(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        body: TransactionCreate,
        response: Response
) -> TransactionRead:
    """Creates a new transaction for `auth_user`."""
    data = create_transaction(db, auth_user, body)
    response.headers['Location'] = f'{router.prefix}/{data.id}'
    return data


@router.put('/{id}')
async def upsert(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str,
        body: TransactionUpdate,
) -> TransactionRead:
    """Upserts `body` to transaction with `id` for `auth_user`."""
    return upsert_transaction(db, auth_user, id, body)


@router.delete('/{id}')
async def delete(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str,
) -> None:
    """Deletes transaction with `id` from `auth_user`."""
    delete_transaction(db, auth_user, id)
