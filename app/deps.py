from typing import Annotated

from fastapi import Cookie, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlmodel import create_engine
from starlette.status import HTTP_401_UNAUTHORIZED

from app.auth.models import AuthSession, AuthUser
from app.config import get_settings


class Cookies(BaseModel):
    session_token: str = Cookie(alias='authjs.session-token')


def get_cookies(cookies: Annotated[Cookies, Cookie()]):
    return cookies


CookiesDep = Annotated[Cookies, Depends(get_cookies)]


def get_db_session():
    engine = create_engine(get_settings().database_url)
    with Session(engine) as session:
        yield session


DBSessionDep = Annotated[Session, Depends(get_db_session)]


def get_auth_user(db: DBSessionDep, cookies: CookiesDep):
    result = db.exec(
        select(AuthSession, AuthUser)
        .join(AuthUser)
        .where(AuthSession.session_token == cookies.session_token)
    ).one_or_none()

    if not result:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid session token')

    auth_session, user = result
    return user


AuthUserDep = Annotated[AuthUser, Depends(get_auth_user)]
