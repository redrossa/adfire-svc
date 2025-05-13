from fastapi import HTTPException, FastAPI
from sqlalchemy.exc import IntegrityError, NoResultFound
from starlette.status import HTTP_409_CONFLICT, HTTP_404_NOT_FOUND


def add_error_handlers(app: FastAPI):
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request, exc):
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(exc))

    @app.exception_handler(NoResultFound)
    async def noresult_error_handler(request, exc):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc))
