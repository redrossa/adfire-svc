from fastapi import Cookie
from pydantic import BaseModel


class Cookies(BaseModel):
    session_token: str = Cookie(alias='authjs.session-token')