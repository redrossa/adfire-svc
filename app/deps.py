from typing import Annotated

from fastapi import Cookie, HTTPException, Depends
from sqlmodel import Session, select
from starlette.status import HTTP_401_UNAUTHORIZED

from app.models.auth import AuthUser
from app.models.cookies import Cookies
from app.db import engine
from app.models import auth


def get_cookies(cookies: Annotated[Cookies, Cookie()]):
    return cookies


CookiesDep = Annotated[Cookies, Depends(get_cookies)]


def get_db_session():
    with Session(engine) as session:
        yield session

DBSessionDep = Annotated[Session, Depends(get_db_session)]


def get_auth_user(db: DBSessionDep, cookies: CookiesDep):
    result = db.exec(
        select(auth.AuthSession, auth.AuthUser)
        .join(auth.AuthUser)
        .where(auth.AuthSession.session_token == cookies.session_token)
    ).one_or_none()

    if not result:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid session token')

    auth_session, user = result
    return user


AuthUserDep = Annotated[AuthUser, Depends(get_auth_user)]