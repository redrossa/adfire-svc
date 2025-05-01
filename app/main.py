from fastapi import FastAPI

from app.routers import transactions, accounts

app = FastAPI()

app.include_router(transactions.routers)

app.include_router(accounts.routers)
