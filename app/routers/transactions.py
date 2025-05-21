from datetime import date
from typing import Self

from fastapi import APIRouter
from pydantic import Field, model_validator, NonNegativeFloat
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.deps import DBSessionDep, AuthUserDep
from app.models import core
from app.models.api_base import ApiBase

routers = APIRouter(
    prefix='/transactions',
    tags=['transactions']
)


class TransactionEntryBody(ApiBase):
    date: date
    amount: NonNegativeFloat
    account_user_id: str | None


class TransactionBody(ApiBase):
    name: str = Field(min_length=1)
    debit_entries: list[TransactionEntryBody] = Field(min_length=1, alias='debits')
    credit_entries: list[TransactionEntryBody] = Field(min_length=1, alias='credits')

    @model_validator(mode='after')
    def check_total_debits_credits_balance(self) -> Self:
        debit_balance = sum(e.amount for e in self.debit_entries)
        credit_balance = sum(e.amount for e in self.credit_entries)
        if debit_balance != credit_balance:
            raise ValueError('Total debit and credit amounts are not balanced')
        return self


class TransactionEntry(TransactionEntryBody):
    id: str


class Transaction(TransactionBody):
    id: str
    debit_entries: list[TransactionEntry] = Field(alias='debits')
    credit_entries: list[TransactionEntry] = Field(alias='credits')
    date: date
    amount: float


class TransactionUpdateBody(TransactionBody):
    debit_entries: list[TransactionEntry] = Field(alias='debits')
    credit_entries: list[TransactionEntry] = Field(alias='credits')
    date: date
    amount: float


def get_account_user_pub_id_to_id_dict(db: DBSessionDep, auth_user: AuthUserDep, pub_ids: list[str]) -> dict[str, int]:
    statement = (select(core.AccountUser.id, core.AccountUser.pub_id)
                 .join(core.Account)
                 .where(core.Account.owner_id == auth_user.id)
                 .where(core.AccountUser.pub_id.in_(pub_ids)))
    results = db.exec(statement).all()
    return {pub_id: id for id, pub_id in results}


def create_transaction_response(t: core.Transaction) -> Transaction:
    debits = [TransactionEntry(
        id=e.pub_id,
        date=e.date,
        amount=-e.amount,
        account_user_id=getattr(e.account_user, 'pub_id', None),
    ) for e in t.entries if e.amount < 0]

    credits = [TransactionEntry(
        id=e.pub_id,
        date=e.date,
        amount=e.amount,
        account_user_id=getattr(e.account_user, 'pub_id', None),
    ) for e in t.entries if e.amount >= 0]

    return Transaction(
        id=t.pub_id,
        name=t.name,
        debits=debits,
        credits=credits,
        date=t.date,
        amount=t.amount,
    )


@routers.get('/', response_model=list[Transaction])
async def get_transactions(db: DBSessionDep, auth_user: AuthUserDep):
    """Returns all transactions belonging to user"""
    stmt = (select(core.Transaction)
            .order_by(core.Transaction.date.desc())
            .options(joinedload(core.Transaction.entries).joinedload(core.TransactionEntry.account_user))
            .where(core.Transaction.owner_id == auth_user.id))

    transactions = db.exec(stmt).unique().all()

    return [create_transaction_response(t) for t in transactions]


@routers.get('/{id}', response_model=Transaction)
async def get_transaction(id: str, db: DBSessionDep, auth_user: AuthUserDep):
    """Returns a transaction by id belonging to user"""
    stmt = (select(core.Transaction)
            .options(joinedload(core.Transaction.entries).joinedload(core.TransactionEntry.account_user))
            .where(core.Transaction.owner_id == auth_user.id)
            .where(core.Transaction.pub_id == id))

    transaction = db.exec(stmt).unique().one()

    return create_transaction_response(transaction)


@routers.post('/', response_model=Transaction)
async def create_transaction(transaction_body: TransactionBody, db: DBSessionDep, auth_user: AuthUserDep):
    pub_id_list = [e.account_user_id for e in transaction_body.debit_entries + transaction_body.credit_entries]
    id_map = get_account_user_pub_id_to_id_dict(db, auth_user, pub_id_list)
    pub_id_map = {v: k for k, v in id_map.items()}

    debit_entries = [core.TransactionEntry(
        date=e.date,
        amount=-e.amount,
        account_user_id=id_map[e.account_user_id]
    ) for e in transaction_body.debit_entries]

    credit_entries = [core.TransactionEntry(
        date=e.date,
        amount=e.amount,
        account_user_id=id_map[e.account_user_id]
    ) for e in transaction_body.credit_entries]

    transaction = core.Transaction(
        name=transaction_body.name,
        entries=debit_entries + credit_entries,
        owner_id=auth_user.id,
        date=min(e.date for e in debit_entries + credit_entries),
        amount=sum(e.amount for e in credit_entries)
    )

    db.add(transaction)
    db.commit()

    debits = [TransactionEntry(
        id=e.pub_id,
        date=e.date,
        amount=-e.amount,
        account_user_id=pub_id_map[e.account_user_id],
    ) for e in transaction.entries if e.amount < 0]

    credits = [TransactionEntry(
        id=e.pub_id,
        date=e.date,
        amount=e.amount,
        account_user_id=pub_id_map[e.account_user_id],
    ) for e in transaction.entries if e.amount >= 0]

    return Transaction(
        id=transaction.pub_id,
        name=transaction.name,
        debits=debits,
        credits=credits,
        date=transaction.date,
        amount=transaction.amount,
    )

@routers.put('/{id}', response_model=Transaction)
async def upsert_transaction(id: str, transaction_body: TransactionUpdateBody, db: DBSessionDep, auth_user: AuthUserDep):
    pub_id_list = [e.account_user_id for e in transaction_body.debit_entries + transaction_body.credit_entries]
    id_map = get_account_user_pub_id_to_id_dict(db, auth_user, pub_id_list)
    pub_id_map = {v: k for k, v in id_map.items()}

    stmt = (select(core.Transaction)
            .options(joinedload(core.Transaction.entries).joinedload(core.TransactionEntry.account_user))
            .where(core.Transaction.owner_id == auth_user.id)
            .where(core.Transaction.pub_id == id))

    transaction = db.exec(stmt).unique().one_or_none()

    if not transaction:
        # transaction doesn't exist => create it with provided public id
        debit_entries = [core.TransactionEntry(
            pub_id=e.pub_id,
            date=e.date,
            amount=-e.amount,
            account_user_id=id_map[e.account_user_id]
        ) for e in transaction_body.debit_entries]

        credit_entries = [core.TransactionEntry(
            pub_id=e.pub_id,
            date=e.date,
            amount=e.amount,
            account_user_id=id_map[e.account_user_id]
        ) for e in transaction_body.credit_entries]

        transaction = core.Transaction(
            pub_id=id,
            name=transaction_body.name,
            entries=debit_entries + credit_entries,
            owner_id=auth_user.id,
            date=min(e.date for e in debit_entries + credit_entries),
            amount=sum(e.amount for e in credit_entries)
        )

        db.add(transaction)
        db.commit()

        debits = [TransactionEntry(
            id=e.pub_id,
            date=e.date,
            amount=-e.amount,
            account_user_id=pub_id_map[e.account_user_id],
        ) for e in transaction.entries if e.amount < 0]

        credits = [TransactionEntry(
            id=e.pub_id,
            date=e.date,
            amount=e.amount,
            account_user_id=pub_id_map[e.account_user_id],
        ) for e in transaction.entries if e.amount >= 0]

        return Transaction(
            id=transaction.pub_id,
            name=transaction.name,
            debits=debits,
            credits=credits,
            date=transaction.date,
            amount=transaction.amount,
        )

    # transaction exists => replace it
    transaction.name = transaction_body.name
    transaction.date = min(e.date for e in transaction_body.debit_entries + transaction_body.credit_entries)
    transaction.amount = sum(e.amount for e in transaction_body.credit_entries)

    old_entries = {e.pub_id: e for e in transaction.entries}
    new_entries_by_id = {e.id: [e, False] for e in transaction_body.debit_entries}
    new_entries_by_id |= {e.id: [e, True] for e in transaction_body.credit_entries}

    for i, (eid, [new_entry, is_credit]) in enumerate(new_entries_by_id.items()):
        # iterate through account users to update or create
        if eid in old_entries:
            # update name and mask
            old_entries[eid].date = new_entry.date
            old_entries[eid].amount = new_entry.amount if is_credit else -new_entry.amount
            old_entries[eid].account_user_id = id_map[new_entry.account_user_id]
        else:
            db.add(core.TransactionEntry(
                pub_id=eid,
                date=new_entry.date,
                amount=new_entry.amount if is_credit else -new_entry.amount,
                transaction_id=transaction.id,
                account_user_id=id_map[new_entry.account_user_id],
            ))

    for eid, old_entry in old_entries.items():
        # iterate through account users to update or delete
        if eid not in new_entries_by_id:
            db.delete(old_entry)

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    debits = [TransactionEntry(
        id=e.pub_id,
        date=e.date,
        amount=-e.amount,
        account_user_id=pub_id_map[e.account_user_id],
    ) for e in transaction.entries if e.amount < 0]

    credits = [TransactionEntry(
        id=e.pub_id,
        date=e.date,
        amount=e.amount,
        account_user_id=pub_id_map[e.account_user_id],
    ) for e in transaction.entries if e.amount >= 0]

    return Transaction(
        id=transaction.pub_id,
        name=transaction.name,
        debits=debits,
        credits=credits,
        date=transaction.date,
        amount=transaction.amount,
    )


@routers.delete('/{id}')
async def delete_transaction(id: str, db: DBSessionDep, auth_user: AuthUserDep):
    stmt = (select(core.Transaction)
            .where(core.Transaction.owner_id == auth_user.id)
            .where(core.Transaction.pub_id == id))

    transaction = db.exec(stmt).one()

    db.delete(transaction)
    db.commit()
