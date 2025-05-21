from datetime import date
from typing import TYPE_CHECKING, Optional

from nanoid import generate
from sqlmodel import Field, Relationship

from app.models.auth import SCHEMA_NAME as AUTH_SCHEMA_NAME
from app.models.core.base import CoreBase, SCHEMA_NAME

if TYPE_CHECKING:
    from app.models.core.accounts import AccountUser


class Transaction(CoreBase, table=True):
    __tablename__ = 'transaction'

    id: int = Field(primary_key=True)
    pub_id: str = Field(index=True, unique=True, default_factory=generate)
    name: str
    date: date
    amount: float

    entries: list['TransactionEntry'] = Relationship(back_populates='transaction', cascade_delete=True)

    owner_id: str = Field(foreign_key=f'{AUTH_SCHEMA_NAME}.user.id', ondelete='CASCADE')


class TransactionEntry(CoreBase, table=True):
    __tablename__ = 'transaction_entry'

    id: int = Field(primary_key=True)
    pub_id: str = Field(index=True, unique=True, default_factory=generate)
    date: date
    amount: float

    transaction_id: int = Field(foreign_key=f'{SCHEMA_NAME}.transaction.id', ondelete='CASCADE')
    transaction: Transaction = Relationship(back_populates='entries')

    account_user_id: int | None = Field(foreign_key=f'{SCHEMA_NAME}.account_user.id', ondelete='SET NULL', nullable=True)
    account_user: Optional['AccountUser'] = Relationship(back_populates='entries')
