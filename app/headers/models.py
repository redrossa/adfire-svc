from pydantic import BaseModel


class CommonHeaders(BaseModel):
    x_session_token: str