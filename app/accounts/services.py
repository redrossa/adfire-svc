from operator import attrgetter

from sqlalchemy import SelectBase
from sqlalchemy.orm import selectinload
from sqlmodel import select, Session

from app.accounts.models import Account, AccountRead, AccountUserRead, AccountCreate, AccountUser, AccountUpdate, \
    AccountBalanceRead, AccountUserBalanceRead
from app.auth.models import AuthUser
from app.transactions.services import aggregate_entries


def map_account(account: Account) -> AccountRead:
    return AccountRead(
        id=account.pub_id,
        name=account.name,
        is_merchant=account.is_merchant,
        users=[AccountUserRead(
            id=u.pub_id,
            name=u.name,
            mask=u.mask
        ) for u in account.users]
    )


def get_all_accounts(db: Session, auth_user: AuthUser, include_merchants: bool = False) -> list[AccountRead]:
    stmt = (select(Account)
            .order_by(Account.name)
            .where(Account.owner_id == auth_user.id))

    if not include_merchants:
        stmt = stmt.where(Account.is_merchant == False)

    accounts = db.exec(stmt).all()

    return [map_account(a) for a in accounts]


def get_account_users_pub_id_to_id_map(db: Session, auth_user: AuthUser, ids: list[str]) -> dict[str, str]:
    statement = (select(AccountUser.id, AccountUser.pub_id)
                 .join(Account)
                 .where(Account.owner_id == auth_user.id)
                 .where(AccountUser.pub_id.in_(ids)))

    results = db.exec(statement).all()

    id_map = {pub_id: id for id, pub_id in results}
    for x in ids:
        if x not in id_map:
            id_map[x] = None

    return id_map


def get_account_by_id_stmt(auth_user: AuthUser, id: str, include_merchants: bool = False) -> SelectBase[Account]:
    stmt = (select(Account)
            .where(Account.owner_id == auth_user.id)
            .where(Account.pub_id == id))

    if not include_merchants:
        stmt = stmt.where(Account.is_merchant == False)

    return stmt


def get_raw_account_by_id(db: Session, auth_user: AuthUser, id: str, include_merchants: bool = False) -> Account:
    return db.exec(get_account_by_id_stmt(auth_user, id, include_merchants)).one()


def get_raw_account_or_none_by_id(db: Session, auth_user: AuthUser, id: str,
                                  include_merchants: bool = False) -> Account | None:
    return db.exec(get_account_by_id_stmt(auth_user, id, include_merchants)).one_or_none()


def get_account_by_id(db: Session, auth_user: AuthUser, id: str, include_merchants: bool = False) -> AccountRead:
    return map_account(get_raw_account_by_id(db, auth_user, id, include_merchants))


def create_account(db: Session, auth_user: AuthUser, account: AccountCreate, id: str = None) -> AccountRead:
    users = [AccountUser(name=u.name, mask=u.mask, order=i) for i, u in enumerate(account.users)]
    account = Account(pub_id=id, name=account.name, is_merchant=account.is_merchant, users=users, owner_id=auth_user.id)

    db.add(account)
    db.commit()

    return map_account(account)


def update_account(db: Session, account: Account, account_in: AccountUpdate) -> AccountRead:
    account.name = account_in.name
    account.is_merchant = account_in.is_merchant

    old_users = {u.pub_id: u for u in account.users}
    new_users_by_id = {u.id: u for u in account_in.users}

    for i, (uid, new_user) in enumerate(new_users_by_id.items()):
        # iterate through new account users to update or create
        if uid in old_users:
            old_users[uid].name = new_user.name
            old_users[uid].mask = new_user.mask
            old_users[uid].order = i
        else:
            db.add(AccountUser(
                pub_id=uid,
                name=new_user.name,
                mask=new_user.mask,
                account_id=account.id,
                order=i
            ))

    for uid, old_user in old_users.items():
        # iterate through old account users to delete
        if uid not in new_users_by_id:
            db.delete(old_user)

    db.add(account)
    db.commit()
    db.refresh(account)

    return map_account(account)


def upsert_account(db: Session, auth_user: AuthUser, id: str, account: AccountUpdate) -> (AccountRead, bool):
    account_raw = get_raw_account_or_none_by_id(db, auth_user, id, include_merchants=True)
    return (create_account(db, auth_user, account, id=id), True) if not account_raw else (
        update_account(db, account_raw, account), False)


def delete_account(db: Session, auth_user: AuthUser, id: str):
    account_raw = get_raw_account_by_id(db, auth_user, id, include_merchants=True)
    db.delete(account_raw)
    db.commit()


def get_account_balances(
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
    account_balances = aggregate_entries(
        sorted((e for users in account.users for e in users.entries), key=attrgetter('date'), reverse=True)
    )
    users = [AccountUserBalanceRead(
        id=u.pub_id,
        name=u.name,
        mask=u.mask,
        balances=aggregate_entries(sorted((e for e in u.entries), key=attrgetter('date'), reverse=True))
    ) for u in account.users]

    return AccountBalanceRead(
        id=account.pub_id,
        name=account.name,
        is_merchant=account.is_merchant,
        balances=account_balances,
        users=users
    )
