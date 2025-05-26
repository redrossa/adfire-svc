from operator import attrgetter

from sqlalchemy.orm import selectinload
from sqlmodel import Session

from app.accounts.balance.models import AccountBalanceRead, AccountUserBalanceRead
from app.accounts.models import Account, AccountUser
from app.accounts.services import get_account_by_id_stmt
from app.auth.models import AuthUser
from app.transactions.services import aggregate_entries


def get_account_balance(
        db: Session,
        auth_user: AuthUser,
        id: str,
        include_merchants: bool = False
) -> AccountBalanceRead:
    stmt = get_account_by_id_stmt(auth_user, id, include_merchants)
    stmt = stmt.options(
        selectinload(Account.users)
        .selectinload(AccountUser.entries)
    )

    account = db.exec(stmt).one()
    account_balances = aggregate_entries(e for users in account.users for e in users.entries)
    users = [AccountUserBalanceRead(
        id=u.pub_id,
        name=u.name,
        mask=u.mask,
        balances=aggregate_entries(e for e in u.entries)
    ) for u in account.users]

    return AccountBalanceRead(
        id=account.pub_id,
        name=account.name,
        is_merchant=account.is_merchant,
        balances=account_balances,
        users=users
    )
