import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database.database import engine, Base
from .endpoints import ping, categories, transactions, elastic

# Create all database tables (if not already present)
Base.metadata.create_all(bind=engine)

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
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(elastic.router, prefix="/elastic", tags=["ElasticSearch"])

logging.basicConfig(level=logging.INFO)
