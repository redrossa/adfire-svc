from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from app.models.auth import AuthUser
from app.models.transactions import TransactionEntity, TransactionBase


def get_all_transactions(db: Session, auth_user: AuthUser) -> list[TransactionEntity]:
    stmt = (select(TransactionEntity)
            .order_by(TransactionEntity.date.desc())
            .where(TransactionEntity.owner_id == auth_user.id))
    transactions = db.exec(stmt).all()
    return transactions


def create_transaction(db: Session, auth_user: AuthUser, base: TransactionBase, id: str = None) -> TransactionEntity:
    entity = TransactionEntity(
        name=base.name,
        date=base.date,
        amount=base.amount,
        is_credit=base.is_credit,
        account=base.account,
        owner_id=auth_user.id,
        id=id,
    )

    db.add(entity)
    db.commit()

    return entity


def update_transaction(db: Session, auth_user: AuthUser, base: TransactionBase, id: str) -> TransactionEntity:
    entity = get_transaction(db, auth_user, id)
    entity.name = base.name
    entity.date = base.date
    entity.amount = base.amount
    entity.is_credit = base.is_credit
    entity.account = base.account

    db.add(entity)
    db.commit()

    return entity


def upsert_transaction(db: Session, auth_user: AuthUser, base: TransactionBase, id: str) -> (TransactionEntity, bool):
    try:
        return update_transaction(db, auth_user, base, id), False
    except NoResultFound:
        return create_transaction(db, auth_user, base, id), True


def get_transaction(db: Session, auth_user: AuthUser, id: str) -> TransactionEntity:
    stmt = (select(TransactionEntity)
            .where(TransactionEntity.id == id)
            .where(TransactionEntity.owner_id == auth_user.id))
    entity = db.exec(stmt).one()
    return entity


def delete_transaction(db: Session, auth_user: AuthUser, id: str):
    entity = get_transaction(db, auth_user, id)
    db.delete(entity)
    db.commit()
