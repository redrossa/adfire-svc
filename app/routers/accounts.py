from fastapi import APIRouter, HTTPException
from pydantic import Field
from sqlalchemy import func
from sqlmodel import select
from starlette.status import HTTP_404_NOT_FOUND

from app.deps import DBSessionDep, AuthUserDep
from app.models import core
from app.models.api_base import ApiBase

routers = APIRouter(
    prefix='/accounts',
    tags=['accounts']
)


class AccountUser(ApiBase):
    name: str = Field(min_length=1)
    mask: str = Field(min_length=1)


class AccountRequest(ApiBase):
    name: str = Field(min_length=1)
    users: list[AccountUser] = Field(min_length=1)


class Account(AccountRequest):
    id: str = Field(min_length=1)


class AccountSynopsis(ApiBase):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    users_count: int


@routers.get('/', response_model=list[AccountSynopsis])
async def get_accounts(db: DBSessionDep, authUser: AuthUserDep):
    """Returns all account synopses belonging to user"""
    result = db.exec(
        select(core.Account.pub_id, core.Account.name, func.count(core.AccountUser.account_id))
        .join(core.AccountUser)
        .where(core.Account.owner_id == authUser.id)
        .group_by(core.Account.id)
    ).all()
    return [AccountSynopsis(
        id=id,
        name=name,
        users_count=users_count
    ) for id, name, users_count in result]


@routers.get('/{id}', response_model=Account)
async def get_account(id: str, db: DBSessionDep, authUser: AuthUserDep):
    """Returns an account by {id} belonging to user"""
    account = db.exec(
        select(core.Account)
        .where(core.Account.owner_id == authUser.id, core.Account.pub_id == id)
    ).one_or_none()

    if not account:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f'Account "{id}" not found')

    return Account(
        id=account.pub_id,
        name=account.name,
        users=[AccountUser(name=u.name, mask=u.mask) for u in account.users]
    )


@routers.post('/', response_model=Account)
async def create_account(accountRequest: AccountRequest, db: DBSessionDep, authUser: AuthUserDep):
    """Creates a new account for this user"""
    users = [core.AccountUser(name=u.name, mask=u.mask) for u in accountRequest.users]
    account = core.Account(name=accountRequest.name, users=users, owner_id=authUser.id)

    db.add(account)
    db.commit()

    return Account(
        id=str(account.pub_id),
        name=account.name,
        users=[AccountUser(name=u.name, mask=u.mask) for u in account.users]
    )


@routers.put('/{id}', response_model=Account)
async def upsert_account(id: str, accountRequest: AccountRequest, db: DBSessionDep, authUser: AuthUserDep):
    """
    Replaces the account by {id} with {accountRequest} if it exists,
    otherwise inserts a new account by {id}
    """
    account = db.exec(
        select(core.Account)
        .where(core.Account.owner_id == authUser.id, core.Account.pub_id == id)
    ).one_or_none()

    if not account:
        # account doesn't exist => create it
        return create_account(accountRequest, db, authUser)

    # account exists => replace it
    existing_by_mask = {u.mask: u for u in account.users}
    incoming_masks = {u.mask for u in accountRequest.users}

    for u in accountRequest.users:
        mask = u.mask
        name = u.name
        if mask in existing_by_mask:
            existing_by_mask[mask].name = name
        else:
            db.add(core.AccountUser(
                name=name,
                mask=mask,
                account_id=account.id
            ))

    for mask, u in existing_by_mask.items():
        if mask not in incoming_masks:
            db.delete(u)

    db.add(account)
    db.commit()
    db.refresh(account)

    return Account(
        id=account.pub_id,
        name=account.name,
        users=[AccountUser(name=u.name, mask=u.mask) for u in account.users],
    )


@routers.delete('/{id}')
async def delete_account(id: str, db: DBSessionDep, authUser: AuthUserDep):
    """Removes the account by {id} belonging to the user"""
    account = db.exec(
        select(core.Account)
        .where(core.Account.owner_id == authUser.id, core.Account.pub_id == id)
    ).one_or_none()

    if not account:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f'Account "{id}" not found')

    db.delete(account)
    db.commit()
