from datetime import date
from decimal import Decimal

from nanoid import generate
from sqlmodel import Field

from app.models.base import CoreBase


class TransactionBase(CoreBase):
    name: str
    date: date
    amount: Decimal = Field(decimal_places=2)
    is_credit: bool
    account: str


class TransactionEntity(TransactionBase, table=True):
    __tablename__ = 'transaction'
    serial: int = Field(primary_key=True)
    id: str = Field(default_factory=generate, index=True, unique=True)
    owner_id: str = Field(foreign_key='authjs.user.id', ondelete='CASCADE')


class Transaction(TransactionBase):
    id: str