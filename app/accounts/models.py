from typing import Self

from nanoid import generate
from pydantic import model_validator
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import declared_attr
from sqlmodel import Field, Relationship

from app.base.models import CoreBase, RouteBase, TimeSeriesPoint
from app.base.services import table_args
from app.transactions.models import TransactionEntry


class Account(CoreBase, table=True):
    __tablename__ = 'account'

    id: int = Field(primary_key=True)
    pub_id: str = Field(index=True, unique=True, default_factory=generate)
    name: str
    is_merchant: bool = Field(default=False)

    users: list['AccountUser'] = Relationship(back_populates='account', cascade_delete=True,
                                              sa_relationship_kwargs={'order_by': 'AccountUser.order'})

    owner_id: str = Field(foreign_key='authjs.user.id', ondelete='CASCADE')

    @declared_attr
    def __table_args__(cls):
        return table_args(cls, (
            UniqueConstraint('owner_id', 'name', name='uniq_owner_name'),
        ))


class AccountUser(CoreBase, table=True):
    __tablename__ = 'account_user'

    id: int = Field(primary_key=True)
    pub_id: str = Field(index=True, unique=True, default_factory=generate)
    name: str
    mask: str
    order: int

    account_id: int = Field(foreign_key='core.account.id', ondelete='CASCADE')
    account: Account = Relationship(back_populates='users')

    entries: list[TransactionEntry] = Relationship(back_populates='account_user')

    @declared_attr
    def __table_args__(cls):
        return table_args(cls, (
            UniqueConstraint('account_id', 'mask', name='uniq_account_mask'),
        ))


# <*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*> Route Models <*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*>

class AccountUserBase(RouteBase):
    name: str
    mask: str


class AccountBase(RouteBase):
    name: str
    is_merchant: bool = False


class AccountUserCreate(AccountUserBase):
    pass


class AccountCreate(AccountBase):
    users: list[AccountUserCreate]

    @model_validator(mode='after')
    def check_no_duplicate_masks(self) -> Self:
        unique_masks = set(u.mask for u in self.users)
        if len(unique_masks) != len(self.users):
            raise ValueError('Account has duplicate user masks')
        return self


class AccountUserUpdate(AccountUserCreate):
    id: str | None = None


class AccountUpdate(AccountCreate):
    users: list[AccountUserUpdate]


class AccountUserRead(AccountUserUpdate):
    id: str


class AccountRead(AccountUpdate):
    id: str
    users: list[AccountUserRead]
