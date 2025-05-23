from fastapi import APIRouter

from app.deps import DBSessionDep, AuthUserDep
from app.transactions.models import TransactionRead, TransactionCreate, TransactionUpdate
from app.transactions.services import get_all_transactions, get_transaction_by_id, create_transaction, \
    upsert_transaction, delete_transaction

router = APIRouter(
    prefix='/transactions',
    tags=['transactions']
)


@router.get('/')
async def get_all(
        db: DBSessionDep,
        auth_user: AuthUserDep
) -> list[TransactionRead]:
    """Returns all transactions from `auth_user`."""
    return get_all_transactions(db, auth_user)


@router.get('/{id}')
async def get(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str
) -> TransactionRead:
    """Returns transaction with `id` from `auth_user`."""
    return get_transaction_by_id(db, auth_user, id)


@router.post('/')
async def create(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        body: TransactionCreate
) -> TransactionRead:
    """Creates a new transaction for `auth_user`."""
    return create_transaction(db, auth_user, body)


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
