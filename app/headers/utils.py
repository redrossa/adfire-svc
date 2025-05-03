from typing import Annotated

from fastapi import Header

from app.headers.models import CommonHeaders

Headers = Annotated[CommonHeaders, Header()]
