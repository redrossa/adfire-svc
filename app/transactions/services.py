from itertools import groupby
from operator import attrgetter

from sqlalchemy.orm import joinedload
from sqlmodel import select, Session

from app.accounts.services import get_account_users_pub_id_to_id_map
from app.auth.models import AuthUser
from app.base.models import TimeSeriesPoint
from app.transactions.models import Transaction, TransactionEntry, TransactionRead, TransactionCreate, \
    TransactionEntryRead, TransactionUpdate, TransactionEntryUpdate


def map_entry(e: TransactionEntry) -> TransactionEntryRead:
    return TransactionEntryRead(
        id=e.pub_id,
        date=e.date,
        amount=abs(e.amount),
        account_user_id=None if not e.account_user else e.account_user.pub_id
    )


def map_transaction(transaction: Transaction) -> TransactionRead:
    return TransactionRead(
        id=transaction.pub_id,
        name=transaction.name,
        date=min(e.date for e in transaction.entries),
        amount=sum(e.amount for e in transaction.entries if e.amount > 0),
        debits=[map_entry(e) for e in transaction.entries if e.amount < 0],
        credits=[map_entry(e) for e in transaction.entries if e.amount >= 0],
    )


def get_all_transactions(db: Session, auth_user: AuthUser):
    stmt = (select(Transaction)
            .order_by(Transaction.date.desc())
            .options(joinedload(Transaction.entries).joinedload(TransactionEntry.account_user))
            .where(Transaction.owner_id == auth_user.id))

    transactions = db.exec(stmt).unique().all()

    return [map_transaction(t) for t in transactions]


def get_transaction_by_id_stmt(auth_user: AuthUser, id: str):
    return (select(Transaction)
            .options(joinedload(Transaction.entries).joinedload(TransactionEntry.account_user))
            .where(Transaction.owner_id == auth_user.id)
            .where(Transaction.pub_id == id))


def get_raw_transaction_or_none_by_id(db: Session, auth_user: AuthUser, id: str) -> Transaction | None:
    stmt = get_transaction_by_id_stmt(auth_user, id)
    return db.exec(stmt).unique().one_or_none()


def get_raw_transaction_by_id(db: Session, auth_user: AuthUser, id: str) -> Transaction:
    stmt = get_transaction_by_id_stmt(auth_user, id)
    return db.exec(stmt).unique().one()


def get_transaction_by_id(db: Session, auth_user: AuthUser, id: str) -> TransactionRead:
    stmt = get_transaction_by_id_stmt(auth_user, id)
    return map_transaction(db.exec(stmt).unique().one())


def create_transaction(db: Session, auth_user: AuthUser, transaction: TransactionCreate) -> TransactionRead:
    account_user_pub_ids = [e.account_user_id for e in transaction.debits + transaction.credits]
    id_map = get_account_users_pub_id_to_id_map(db, auth_user, account_user_pub_ids)

    debits = [TransactionEntry(
        date=e.date,
        amount=-e.amount,
        account_user_id=id_map[e.account_user_id]
    ) for e in transaction.debits]

    credits = [TransactionEntry(
        date=e.date,
        amount=e.amount,
        account_user_id=id_map[e.account_user_id]
    ) for e in transaction.credits]

    transaction = Transaction(
        name=transaction.name,
        entries=debits + credits,
        owner_id=auth_user.id,
        date=min(e.date for e in debits + credits),
        amount=sum(e.amount for e in credits)
    )

    db.add(transaction)
    db.commit()

    return map_transaction(transaction)


def update_transaction(
        db: Session,
        auth_user: AuthUser,
        transaction: Transaction,
        transaction_in: TransactionUpdate
) -> TransactionRead:
    account_user_pub_ids = [e.account_user_id for e in transaction_in.debits + transaction_in.credits if
                            e.account_user_id is not None]
    id_map = get_account_users_pub_id_to_id_map(db, auth_user, account_user_pub_ids)

    transaction.name = transaction_in.name
    transaction.date = min(e.date for e in transaction_in.debits + transaction_in.credits)
    transaction.amount = sum(e.amount for e in transaction_in.credits)

    old_entries = {e.pub_id: e for e in transaction.entries}
    new_entry_ids = set()

    def iterate_incoming_entries(entries: list[TransactionEntryUpdate], is_credit: bool):
        for e in entries:
            # iterate to update or create entries
            if e.id in old_entries:
                # update name and mask
                old_entries[e.id].date = e.date
                old_entries[e.id].amount = e.amount if is_credit else -e.amount
                old_entries[e.id].account_user_id = id_map.get(e.account_user_id, None)
            else:
                db.add(TransactionEntry(
                    pub_id=e.id,
                    date=e.date,
                    amount=e.amount if is_credit else -e.amount,
                    transaction_id=transaction.id,
                    account_user_id=id_map.get(e.account_user_id, None),
                ))
            new_entry_ids.add(e.id)

    iterate_incoming_entries(transaction_in.debits, False)
    iterate_incoming_entries(transaction_in.credits, True)

    for eid, old_entry in old_entries.items():
        # iterate to delete entries
        if eid not in new_entry_ids:
            db.delete(old_entry)

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return map_transaction(transaction)


def upsert_transaction(
        db: Session,
        auth_user: AuthUser,
        id: str,
        transaction: TransactionUpdate
) -> TransactionRead:
    transaction_raw = get_raw_transaction_or_none_by_id(db, auth_user, id)
    return create_transaction(db, auth_user, transaction) \
        if not transaction_raw \
        else update_transaction(db, auth_user, transaction_raw, transaction)


def delete_transaction(db: Session, auth_user: AuthUser, id: str):
    transaction_raw = get_raw_transaction_by_id(db, auth_user, id)
    db.delete(transaction_raw)
    db.commit()


def aggregate_entries(sorted_entries: list[TransactionEntry]) -> list[TimeSeriesPoint]:
    return [TimeSeriesPoint(
        amount=sum(x.amount for x in group),
        date=key
    ) for key, group in groupby(sorted_entries, key=attrgetter('date'))]
