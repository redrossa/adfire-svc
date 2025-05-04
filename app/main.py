from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import AuthDep
from app.db.models import Users
from app.routers import transactions, accounts

app = FastAPI()

origins = [
    'http://localhost:3000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.routers)

app.include_router(accounts.routers)


@app.get('/whoami')
async def whoami(user: Users = AuthDep):
    return user
