from app.accounts.models import AccountUserRead, AccountRead
from app.base.models import TimeSeriesPoint


class AccountUserBalanceRead(AccountUserRead):
    balances: list[TimeSeriesPoint]


class AccountBalanceRead(AccountRead):
    balances: list[TimeSeriesPoint]
    users: list[AccountUserBalanceRead]