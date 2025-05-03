from datetime import datetime

from sqlmodel import SQLModel, Field


class Users(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    name: str | None
    email: str | None
    emailVerified: datetime | None
    image: str | None


class Sessions(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    userId: int = Field(foreign_key='users.id')
    expires: datetime
    sessionToken: str
