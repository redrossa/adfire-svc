from fastapi import FastAPI

from app.auth import AuthDep
from app.db.models import Users
from app.routers import transactions, accounts

app = FastAPI()

app.include_router(transactions.routers)

app.include_router(accounts.routers)


@app.get('/whoami')
async def whoami(user: Users = AuthDep):
    return user
