from datetime import date
from typing import TYPE_CHECKING, Optional

from nanoid import generate
from pydantic import PositiveFloat
from sqlmodel import Field, Relationship

from app.base.models import CoreBase, RouteBase

if TYPE_CHECKING:
    from app.accounts.models import AccountUser


class Transaction(CoreBase, table=True):
    __tablename__ = 'transaction'

    id: int = Field(primary_key=True)
    pub_id: str = Field(index=True, unique=True, default_factory=generate)
    name: str
    date: date
    amount: float

    entries: list['TransactionEntry'] = Relationship(back_populates='transaction', cascade_delete=True)

    owner_id: str = Field(foreign_key='authjs.user.id', ondelete='CASCADE')


class TransactionEntry(CoreBase, table=True):
    __tablename__ = 'transaction_entry'

    id: int = Field(primary_key=True)
    pub_id: str = Field(index=True, unique=True, default_factory=generate)
    date: date
    amount: float

    transaction_id: int = Field(foreign_key='core.transaction.id', ondelete='CASCADE')
    transaction: Transaction = Relationship(back_populates='entries')

    account_user_id: int | None = Field(foreign_key='core.account_user.id', ondelete='SET NULL', nullable=True)
    account_user: Optional['AccountUser'] = Relationship(back_populates='entries')


# <*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*> Route Models <*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*>

class TransactionEntryBase(RouteBase):
    date: date
    amount: PositiveFloat
    account_user_id: str | None


class TransactionBase(RouteBase):
    name: str


class TransactionEntryCreate(TransactionEntryBase):
    pass


class TransactionCreate(TransactionBase):
    debits: list[TransactionEntryCreate]
    credits: list[TransactionEntryCreate]


class TransactionEntryUpdate(TransactionEntryCreate):
    id: str


class TransactionUpdate(TransactionCreate):
    debits: list[TransactionEntryUpdate]
    credits: list[TransactionEntryUpdate]


class TransactionEntryRead(TransactionEntryUpdate):
    pass


class TransactionRead(TransactionUpdate):
    id: str
    date: date
    amount: float
    debits: list[TransactionEntryRead]
    credits: list[TransactionEntryRead]
