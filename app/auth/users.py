from fastapi import HTTPException, Depends
from sqlmodel import select

from app.db import SessionDep
from app.db.models import Sessions, Users
from app.headers import Headers


def get_user(headers: Headers, session: SessionDep):
    result = session.exec(
        select(Sessions, Users)
        .join(Users)
        .where(Sessions.sessionToken == headers.x_session_token)
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail='Invalid session token')
    auth_session, user = result
    return user


AuthDep = Depends(get_user)