from typing import Annotated

from fastapi import Depends
from sqlmodel import create_engine, Session

from app.config import get_settings
from app.db.models import Sessions

engine = create_engine(get_settings().database_url)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Sessions, Depends(get_session)]
