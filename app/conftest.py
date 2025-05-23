from datetime import datetime, timedelta

import pytest
from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.sql.ddl import CreateSchema
from sqlalchemy_utils import create_database, database_exists, drop_database
from sqlmodel import Session, SQLModel, create_engine
from starlette.testclient import TestClient

from app.auth.models import AuthSession, AuthUser
from app.base.models import AuthBase, CoreBase
from app.config import get_settings
from app.deps import get_db_session
from app.main import app
from app.deps import Cookies


def pytest_configure(config):
    load_dotenv('.env.test')


@pytest.fixture
def session_token():
    return 'coneofsilence'


@pytest.fixture
def cookies(session_token: str):
    return {'authjs.session-token': session_token}


@pytest.fixture
def auth_user():
    return AuthUser(
        id='redrossa-user',
        name='redrossa',
        email='redrossa@adfire.com',
    )


@pytest.fixture
def auth_session(session_token: str, auth_user: AuthUser):
    return AuthSession(
        id='redrossa-session',
        session_token=session_token,
        expires=datetime.now() + timedelta(hours=12),
        user=auth_user,
    )


@pytest.fixture
def session(auth_session: AuthSession):
    settings = get_settings()

    if database_exists(settings.database_url):
        drop_database(settings.database_url)

    create_database(settings.database_url)

    event.listen(AuthBase.metadata, 'before_create', CreateSchema('authjs', if_not_exists=True))
    event.listen(CoreBase.metadata, 'before_create', CreateSchema('core', if_not_exists=True))

    engine = create_engine(settings.database_url)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(auth_session)
        session.commit()
        yield session

    drop_database(settings.database_url)


@pytest.fixture
def client(session: Session, cookies: Cookies):
    def get_session_override():
        return session

    app.dependency_overrides[get_db_session] = get_session_override

    client = TestClient(app, cookies=cookies)
    yield client

    app.dependency_overrides.clear()
