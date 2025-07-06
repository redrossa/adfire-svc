from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.deps import AuthUserDep
from app.errors import add_error_handlers
from app.models.auth import AuthUser
from app.routers.transactions import router as transactions_router

app = FastAPI()

add_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(transactions_router)


@app.get('/whoami')
async def whoami(auth_user: AuthUserDep) -> AuthUser:
    return auth_user
