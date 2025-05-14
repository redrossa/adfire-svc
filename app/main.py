from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.deps import AuthUserDep
from app.errors import add_error_handlers
from app.routers import transactions, accounts

app = FastAPI()

add_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(transactions.routers)
app.include_router(accounts.routers)


@app.get('/whoami')
async def whoami(auth_user: AuthUserDep):
    return auth_user
