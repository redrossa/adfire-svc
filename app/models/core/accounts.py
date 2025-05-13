from nanoid import generate
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import declared_attr
from sqlmodel import Field, Relationship

from app.models._utils import table_args
from app.models.auth import SCHEMA_NAME as AUTH_SCHEMA_NAME
from app.models.core.base import CoreBase, SCHEMA_NAME
from app.models.core.transactions import TransactionEntry


class Account(CoreBase, table=True):
    __tablename__ = 'account'

    id: int = Field(primary_key=True)
    pub_id: str = Field(index=True, unique=True, default_factory=generate)
    name: str
    is_merchant: bool = Field(default=False)

    users: list['AccountUser'] = Relationship(back_populates='account', cascade_delete=True)

    owner_id: str = Field(foreign_key=f'{AUTH_SCHEMA_NAME}.user.id', ondelete='CASCADE')

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

    account_id: int = Field(foreign_key=f'{SCHEMA_NAME}.account.id', ondelete='CASCADE')
    account: Account = Relationship(back_populates='users')

    entries: list[TransactionEntry] = Relationship(back_populates='account_user')

    @declared_attr
    def __table_args__(cls):
        return table_args(cls, (
            UniqueConstraint('account_id', 'mask', name='uniq_account_mask'),
        ))
