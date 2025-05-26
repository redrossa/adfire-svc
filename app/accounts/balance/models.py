from app.accounts.models import AccountUserRead, AccountRead
from app.base.models import TimeSeries


class AccountUserBalanceRead(AccountUserRead):
    balances: list[TimeSeries]


class AccountBalanceRead(AccountRead):
    balances: list[TimeSeries]
    users: list[AccountUserBalanceRead]