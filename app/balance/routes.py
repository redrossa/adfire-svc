from fastapi import APIRouter

from app.balance.models import Balance
from app.balance.services import get_balances
from app.deps import DBSessionDep, AuthUserDep

router = APIRouter(
    prefix='/balance',
    tags=['balance']
)


@router.get('/')
async def get(db: DBSessionDep, auth_user: AuthUserDep) -> Balance:
    return get_balances(db, auth_user)
