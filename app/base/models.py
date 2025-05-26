from datetime import date

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import SQLModel


class CoreBase(SQLModel):
    __table_args__ = {'schema': 'core'}

class AuthBase(SQLModel):
    __table_args__ = {'schema': 'authjs'}

class RouteBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra='forbid'
    )


class TimeSeries(RouteBase):
    date: date
    amount: float
    cumulative: float
