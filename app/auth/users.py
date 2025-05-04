from typing import Annotated

from fastapi import HTTPException, Depends, Cookie
from sqlmodel import select

from app.cookies import Cookies
from app.db import SessionDep
from app.db.models import Sessions, Users


def get_user(cookies: Annotated[Cookies, Cookie()], session: SessionDep):
    result = session.exec(
        select(Sessions, Users)
        .join(Users)
        .where(Sessions.sessionToken == cookies.session_token)
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail='Invalid session token')
    auth_session, user = result
    return user


AuthDep = Depends(get_user)