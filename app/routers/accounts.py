from typing import Self

from fastapi import APIRouter, HTTPException
from pydantic import Field, model_validator
from sqlmodel import select
from starlette.status import HTTP_404_NOT_FOUND

from app.deps import DBSessionDep, AuthUserDep
from app.models import core
from app.models.api_base import ApiBase

routers = APIRouter(
    prefix='/accounts',
    tags=['accounts']
)


class AccountUserBody(ApiBase):
    name: str = Field(min_length=1)
    mask: str = Field(min_length=1)


class AccountUser(AccountUserBody):
    id: str | None = Field(default=None)


class AccountBody(ApiBase):
    name: str = Field(min_length=1)
    is_merchant: bool = Field(default=False)
    users: list[AccountUserBody] = Field(min_length=1)

    @model_validator(mode='after')
    def check_no_duplicate_user_masks(self) -> Self:
        unique_masks = set(u.mask for u in self.users)
        if len(unique_masks) != len(self.users):
            raise ValueError('Contains duplicate masks')
        return self


class AccountBodyUpdate(AccountBody):
    users: list[AccountUser] = Field(min_length=1)

    @model_validator(mode='after')
    def check_no_duplicate_user_ids(self) -> Self:
        ids = [u.id for u in self.users]
        unique_ids = set(ids)
        if len(unique_ids) != len(ids):
            raise ValueError('Contains duplicate IDs')
        return self


class Account(AccountBody):
    id: str = Field(min_length=1)
    users: list[AccountUser] = Field(min_length=1)


@routers.get('/', response_model=list[Account])
async def get_accounts(
        db: DBSessionDep,
        auth_user: AuthUserDep,
        include_merchants: bool = False,
):
    """Returns all accounts belonging to user"""
    stmt = select(core.Account).where(core.Account.owner_id == auth_user.id)

    if not include_merchants:
        stmt = stmt.where(core.Account.is_merchant == False)

    accounts = db.exec(stmt).all()

    return [Account(
        id=a.pub_id,
        name=a.name,
        is_merchant=a.is_merchant,
        users=[AccountUser(id=u.pub_id, name=u.name, mask=u.mask) for u in a.users]
    ) for a in accounts]


@routers.get('/{id}', response_model=Account)
async def get_account(
        id: str,
        db: DBSessionDep, auth_user:
        AuthUserDep,
        include_merchants: bool = False,
):
    """Returns an account by {id} belonging to user"""
    stmt = (select(core.Account)
            .where(core.Account.owner_id == auth_user.id)
            .where(core.Account.pub_id == id))

    if not include_merchants:
        stmt = stmt.where(core.Account.is_merchant == False)

    account = db.exec(stmt).one_or_none()

    if not account:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f'Account "{id}" not found')

    return Account(
        id=account.pub_id,
        name=account.name,
        is_merchant=account.is_merchant,
        users=[AccountUser(id=u.pub_id, name=u.name, mask=u.mask) for u in account.users]
    )


@routers.post('/', response_model=Account)
async def create_account(
        account_body: AccountBody,
        db: DBSessionDep,
        auth_user: AuthUserDep
):
    """Creates a new account for this user"""
    users = [core.AccountUser(name=u.name, mask=u.mask) for u in account_body.users]
    account = core.Account(name=account_body.name, users=users, owner_id=auth_user.id)

    db.add(account)
    db.commit()

    return Account(
        id=account.pub_id,
        name=account.name,
        is_merchant=account.is_merchant,
        users=[AccountUser(id=u.pub_id, name=u.name, mask=u.mask) for u in account.users]
    )


@routers.put('/{id}', response_model=Account)
async def upsert_account(
        id: str,
        account_body: AccountBodyUpdate,
        db: DBSessionDep,
        auth_user: AuthUserDep
):
    """
    Replaces the account by {id} with {accountRequest} if it exists,
    otherwise inserts a new account by {id}
    """
    stmt = (select(core.Account)
            .where(core.Account.owner_id == auth_user.id)
            .where(core.Account.pub_id == id))

    account = db.exec(stmt).one_or_none()

    if not account:
        # account doesn't exist => create it with provided public id
        users = [core.AccountUser(pub_id=u.id, name=u.name, mask=u.mask) for u in account_body.users]
        account = core.Account(pub_id=id, name=account_body.name, users=users, owner_id=auth_user.id)

        db.add(account)
        db.commit()

        return Account(
            id=account.pub_id,
            name=account.name,
            is_merchant=account.is_merchant,
            users=[AccountUser(id=u.pub_id, name=u.name, mask=u.mask) for u in account.users]
        )

    # account exists => replace it
    account.name = account_body.name

    old_users = {u.pub_id: u for u in account.users}
    new_users_by_id = {u.id: u for u in account_body.users}
    new_users_by_mask = {u.mask: u for u in account_body.users}

    for uid, new_user in new_users_by_id.items():
        # iterate through account users to update or create
        if uid in old_users:
            # update name and mask
            old_users[uid].name = new_user.name
            old_users[uid].mask = new_user.mask
        else:
            db.add(core.AccountUser(
                pub_id=uid,
                name=new_user.name,
                mask=new_user.mask,
                account_id=account.id
            ))

    for uid, old_user in old_users.items():
        # iterate through account users to update or delete
        if uid not in new_users_by_id:
            db.delete(old_user)

    db.add(account)
    db.commit()
    db.refresh(account)

    return Account(
        id=account.pub_id,
        name=account.name,
        is_merchant=account.is_merchant,
        users=[AccountUser(id=u.pub_id, name=u.name, mask=u.mask) for u in account.users],
    )


@routers.delete('/{id}')
async def delete_account(
        id: str,
        db: DBSessionDep,
        auth_user: AuthUserDep
):
    """Removes the account by {id} belonging to the user"""
    stmt = (select(core.Account)
            .where(core.Account.owner_id == auth_user.id)
            .where(core.Account.pub_id == id))

    account = db.exec(stmt).one_or_none()

    if not account:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f'Account "{id}" not found')

    db.delete(account)
    db.commit()
