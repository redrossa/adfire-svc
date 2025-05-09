from fastapi import HTTPException, FastAPI
from sqlalchemy.exc import IntegrityError
from starlette.status import HTTP_409_CONFLICT


def add_error_handlers(app: FastAPI):
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request, exc):
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(exc))
