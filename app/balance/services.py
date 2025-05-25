from operator import attrgetter

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.accounts.models import Account, AccountUser
from app.auth.models import AuthUser
from app.balance.models import Balance
from app.transactions.services import aggregate_entries


def get_balances(db: Session, auth_user: AuthUser, ) -> Balance:
    stmt = (
        select(Account)
        .where(Account.owner_id == auth_user.id)
        .where(Account.is_merchant == False)
        .options(
            selectinload(Account.users)
            .selectinload(AccountUser.entries)
        )
    )

    accounts = db.exec(stmt).all()

    return Balance(
        balances=aggregate_entries(
            sorted((e for a in accounts for u in a.users for e in u.entries), key=attrgetter('date'))
        )
    )
