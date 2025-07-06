from fastapi import APIRouter, Response
from starlette.status import HTTP_201_CREATED

from app.deps import DBSessionDep, AuthUserDep
from app.models.transactions import Transaction, TransactionEntity, TransactionBase
from app.services.transactions import get_all_transactions, create_transaction, upsert_transaction, get_transaction, \
    delete_transaction

router = APIRouter(
    prefix='/transactions',
    tags=['transactions']
)


@router.get('/', response_model=list[Transaction])
async def get_all(
        db: DBSessionDep,
        auth_user: AuthUserDep,
) -> list[TransactionEntity]:
    return get_all_transactions(db, auth_user)


@router.post('/', response_model=Transaction, status_code=HTTP_201_CREATED)
async def create(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        base: TransactionBase,
        response: Response
) -> TransactionEntity:
    data = create_transaction(db, auth_user, base)
    response.headers['Location'] = f'{router.prefix}/{data.id}'
    return data


@router.put('/{id}', response_model=Transaction)
async def upsert(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        base: TransactionBase,
        id: str,
        response: Response
) -> TransactionEntity:
    data, is_created = upsert_transaction(db, auth_user, base, id)

    if is_created:
        response.status_code = HTTP_201_CREATED
        response.headers['Location'] = f'{router.prefix}/{data.id}'

    return data


@router.get('/{id}', response_model=Transaction)
async def get(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str,
) -> TransactionEntity:
    return get_transaction(db, auth_user, id)


@router.delete('/{id}')
async def delete(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        id: str,
):
    delete_transaction(db, auth_user, id)
