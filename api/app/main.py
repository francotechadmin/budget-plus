import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database.database import engine, Base
from .models.models import Base
from .endpoints import ping, categories, users, transactions_crud, transactions_reporting, transactions_import

app = FastAPI(title="Production-Ready API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with optional prefixes and tags
app.include_router(ping.router)
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(transactions_crud.router, prefix="/transactions")
app.include_router(transactions_reporting.router, prefix="/transactions")
app.include_router(transactions_import.router, prefix="/transactions")
app.include_router(users.router, prefix="/users", tags=["Users"])

logging.basicConfig(level=logging.DEBUG)
