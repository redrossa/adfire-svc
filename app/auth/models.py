from datetime import datetime

from sqlmodel import Field, Relationship

from app.base.models import AuthBase


class AuthUser(AuthBase, table=True):
    __tablename__ = 'user'

    id: str = Field(primary_key=True)
    name: str | None
    email: str | None
    email_verified: datetime | None
    image: str | None

    accounts: list['AuthAccount'] = Relationship(back_populates='user')
    sessions: list['AuthSession'] = Relationship(back_populates='user')


class AuthAccount(AuthBase, table=True):
    __tablename__ = 'account'

    id: str = Field(primary_key=True)
    type: str
    provider: str
    provider_account_id: str
    refresh_token: str | None
    access_token: str | None
    expires_at: int | None
    token_type: str | None
    scope: str | None
    id_token: str | None
    session_state: str | None

    user_id: str = Field(foreign_key='authjs.user.id', ondelete='RESTRICT')
    user: AuthUser = Relationship(back_populates='accounts')


class AuthSession(AuthBase, table=True):
    __tablename__ = 'session'

    id: str = Field(primary_key=True)
    session_token: str
    expires: datetime

    user_id: str = Field(foreign_key='authjs.user.id', ondelete='RESTRICT')
    user: AuthUser = Relationship(back_populates='sessions')


class AuthVerificationToken(AuthBase, table=True):
    __tablename__ = 'verification_token'

    identifier: str = Field(primary_key=True)
    token: str = Field(primary_key=True)
    expires: datetime
