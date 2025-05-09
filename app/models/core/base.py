from sqlmodel import SQLModel

SCHEMA_NAME = 'core'


class CoreBase(SQLModel):
    __table_args__ = {'schema': SCHEMA_NAME}
