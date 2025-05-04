from typing import List, Annotated

from annotated_types import MinLen
from fastapi import APIRouter
from pydantic import BaseModel

from app.auth import AuthDep
from app.db import Users

routers = APIRouter(
    prefix='/accounts',
    tags=['accounts']
)


class User(BaseModel):
    name: Annotated[str, MinLen(1)]
    mask: Annotated[str, MinLen(1)]


class Account(BaseModel):
    name: Annotated[str, MinLen(1)]
    users: Annotated[List[User], MinLen(1)]


@routers.get('/')
async def get_accounts():
    """Returns all accounts belonging to user"""
    return [
        {
            'id': 'cma5vgtvz00020ck0757f1rri',
            'name': 'Chase Total Checking',
            'usersCount': 1
        },
        {
            'id': 'cma5vgtvz00030ck03pd4chhn',
            'name': 'Chase Freedom Unlimited',
            'usersCount': 1
        },
        {
            'id': 'cma5vgtvz00040ck0ap7t2qho',
            'name': 'Amex Gold',
            'usersCount': 2
        }
    ]


@routers.get('/{id}')
async def get_account(id: str):
    """Returns an account by id belonging to user"""
    return {
        'id': 'cma5vgtvz00040ck0ap7t2qho',
        'name': 'Amex Gold',
        'users': [
            {'name': 'John Doe', 'mask': '0001'},
            {'name': 'Jane Doe', 'mask': '0002'}
        ]
    }


@routers.post('/')
async def create_account(account: Account, user: Users = AuthDep):
    """Creates a new account for this user"""
    return account
