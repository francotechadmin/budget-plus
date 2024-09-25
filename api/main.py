import  os, logging, io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
from elasticsearch_simple_client.uploader import Uploader
from elasticsearch_simple_client.searcher import Searcher
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import and_
import calendar


logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PG_DBNAME = os.getenv("PG_DBNAME", "postgres")
PG_HOST = os.getenv("PG_HOST", "db")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "mysecretpassword")
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}/{PG_DBNAME}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Transaction model definition
class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    date = Column(Date)
    amount = Column(Float)
    category = Column(String)
    section = Column(String)
    is_indexed = Column(Integer, default=0)

# Categories table definition
class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    section = Column(String, index=True)
    category = Column(String, index=True)

# Define a Pydantic model for the request body
class DescriptionRequest(BaseModel):
    description: str

# update transaction
class UpdateTransactionRequest(BaseModel):
    transaction_id: int
    category: str


def create_db():
    Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @app.on_event("startup")
# def on_startup():
#     create_db()

# ping
@app.get("/ping")
async def pong():
    return {"ping": "pong!"}

# Get all categories
@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    categories_by_section = {}
    for category in categories:
        if category.section not in categories_by_section:
            categories_by_section[category.section] = []
        categories_by_section[category.section].append(category.category)

    return categories_by_section

#update categories
@app.post("/update-categories/")
async def update_categories(file: Annotated[UploadFile, Form(...)], db: Session = Depends(get_db)):
    """Update categories in the database"""

    logging.info("Updating categories...")
    df = pd.read_excel(io.BytesIO(file.file.read()))

    for _, row in df.iterrows():
        category = Category(
            section=row['section'],
            category=row['category']
        )
        db.add(category)

    db.commit()
    logging.info("Categories updated.")
    return {"message": "Categories updated."}

# Update transaction
@app.post("/update-transaction/")
async def update_transaction(update_request: UpdateTransactionRequest, db: Session = Depends(get_db)):
    """Update a transaction's category"""

    transaction_id = update_request.transaction_id
    category = update_request.category

    logging.info(f"Updating transaction {transaction_id}...")
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    # get all  transactions with the same description or are similar to the first 20 characters if the description is long
    # similar_transactions = db.query(Transaction).filter(
    #     Transaction.description.like(f"%{transaction.description[:20]}%")
    # ).all()
    similar_transactions = []

    if transaction:
        transaction.category = category
        transaction.section = db.query(Category).filter(Category.category == category).first().section
        db.commit()
        logging.info(f"Transaction {transaction_id} updated.")

        # add to elasticsearch
        searcher = Uploader()
        searcher.post_df(pd.DataFrame([{
            'description': transaction.description,
            'annotated_category': category
        }]))

        # update similar transactions
        for similar_transaction in similar_transactions:
            similar_transaction.category = category
            similar_transaction.section = db.query(Category).filter(Category.category == category).first().section
            db.commit()

        return get_transactions(db)
    else:
        raise HTTPException(status_code=404, detail="Transaction not found.")

# Upload transaction files
@app.post("/transactions/")
async def upload_bank_transactions(files: list[UploadFile], db: Session = Depends(get_db)):
    """Upload bank transactions to the database"""

    print(f"Uploading {len(files)} files...")
    
    # Type of bank records
    chase_debit_columns = ['Details', 'Posting Date', 'Description', 'Amount', 'Type', 'Balance', 'Check or Slip #']
    chase_credit_columns = ['Transaction Date', 'Post Date', 'Description', 'Category', 'Type', 'Amount', 'Memo']
    citi_columns = ['Status', 'Date', 'Description', 'Debit', 'Credit']


    # check column names to determine source
    source = ''

    for file in files:
        try:
            df_preview = pd.read_csv(file.file, nrows=1)  # Read first row to check columns
            if 'Posting Date' in df_preview.columns:
                source = 'chase_debit'
            elif 'Post Date' in df_preview.columns:
                source = 'chase_credit'
            elif 'Date' in df_preview.columns:
                source = 'citi'
            print(f"Transactions Source: {source}")
            if not source:
                raise HTTPException(status_code=400, detail="Unsupported file format.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

        # Reset file pointer to beginning after the first read
        file.file.seek(0)

        # Read the uploaded file
        try:
            if source == 'chase_debit':
                df = pd.read_csv(file.file, usecols=chase_debit_columns)
                # Rename columns to match the DB schema
                df = df.rename(columns={
                    'Description': 'description',
                    'Posting Date': 'date',
                    'Amount': 'amount',
                })
            elif source == 'citi':
                print(f"Attempting to read citi file {file.filename}")
                # put debit and credit in one column
                df = pd.read_csv(file.file, usecols=citi_columns)
                df['amount'] = df['Debit'].fillna(0) * -1 + df['Credit'].fillna(0) * -1
                # Rename columns to match the DB schema
                df = df.rename(columns={
                    'Description': 'description',
                    'Date': 'date',
                })
                # Filter out rows where amount is NaN
                df = df[df['amount'].notna()]
                print(df.head())

            else:
                df = pd.read_csv(file.file, usecols=chase_credit_columns)
                # Rename columns to match the DB schema
                df = df.rename(columns={
                    'Description': 'description',
                    'Post Date': 'date',
                    'Amount': 'amount',
                })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

        new_transactions = []
        searcher = Searcher()
        
        for _, row in df.iterrows():
            # Check if the transaction already exists (based on description, date, and amount)
            existing_transaction = db.query(Transaction).filter(
                and_(
                    Transaction.description == row['description'],
                    Transaction.date == row['date'],
                    Transaction.amount == row['amount']
                )
            ).first()
            
            # If the transaction does not exist, add it to the database
            if not existing_transaction:
                category = searcher.execute_search(field="description", shoulds=[row['description']])["hits"]["hits"]
                new_transaction = Transaction(
                    description=row['description'],
                    date=row['date'],
                    amount=row['amount'],
                    category=category[0]["_source"]["annotated_category"] if category else "Uncategorized",
                    section=db.query(Category).filter(Category.category == category[0]["_source"]["annotated_category"]).first().section if category else "Uncategorized"
                )
                new_transactions.append(new_transaction)

        # Bulk insert new transactions
        if new_transactions:
            db.bulk_save_objects(new_transactions)
            db.commit()
            logging.info(f"Inserted {len(new_transactions)} new transactions into the database.")
        else:
            logging.info("No new transactions to insert.")

    return get_transactions(db)

# Get all transactions
@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    # sort from newest to oldest and by name
    transactions = sorted(transactions, key=lambda x: (x.date, x.description) , reverse=True)
    return transactions

# Get transactions for year-month grouped by category
@app.get("/transactions/{year}/{month}")
def get_transactions_by_month(year: int, month: int, db: Session = Depends(get_db)):
    start_date = f"{year}-{month:02d}-01"
    # Get the last day of the month using calendar.monthrange
    last_day = calendar.monthrange(year, month)[1]

    # End date is the last day of the month
    end_date = f"{year}-{month:02d}-{last_day}"

    transactions = db.query(Transaction).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
    ).all()

    # Group transactions by category
    grouped_transactions = {}
    for transaction in transactions:
        if transaction.section not in grouped_transactions:
            grouped_transactions[transaction.section] = {}
        if transaction.category not in grouped_transactions[transaction.section]:
            grouped_transactions[transaction.section][transaction.category] = []
        grouped_transactions[transaction.section][transaction.category].append(transaction)

    # sort by section and category and put income section first
    sorted_grouped_transactions = {}
    if "Income" in grouped_transactions:
        sorted_grouped_transactions["Income"] = grouped_transactions["Income"]
        del grouped_transactions["Income"]
        
    for section, categories in sorted(grouped_transactions.items()):
        sorted_grouped_transactions[section] = categories
    return sorted_grouped_transactions

# Get transactions totals for year-months by category
@app.get("/transactions/expenses/{year}/{month}")
def get_transactions_totals(year: int, month: int, db: Session = Depends(get_db)):
    start_date = f"{year}-{month:02d}-01"
    # Get the last day of the month using calendar.monthrange
    last_day = calendar.monthrange(year, month)[1]

    # End date is the last day of the month
    end_date = f"{year}-{month:02d}-{last_day}"

    transactions = db.query(Transaction).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.section != 'Income',
        Transaction.category != 'Transfer',

    ).all()

    # Calculate totals by category
    totals = {}
    for transaction in transactions:
        if transaction.category not in totals:
            totals[transaction.category] = 0
        totals[transaction.category] += transaction.amount

    return totals

# get total income and expenses for year-month
@app.get("/transactions/totals/{year}/{month}")
def get_transactions_totals(year: int, month: int, db: Session = Depends(get_db)):
    start_date = f"{year}-{month:02d}-01"
    # Get the last day of the month using calendar.monthrange
    last_day = calendar.monthrange(year, month)[1]

    # End date is the last day of the month
    end_date = f"{year}-{month:02d}-{last_day}"

    logging.info(f"Getting totals for transactions from {start_date} to {end_date}...")

    transactions = db.query(Transaction).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()

    income_total = sum(t.amount for t in transactions if t.section == 'Income')
    expenses_total = sum(t.amount for t in transactions if t.section != 'Income')

    return {
        "income": income_total,
        "expenses": expenses_total
    }

# Get income and expenses for last six months only {"September 2024": {"income": 1000, "expenses": 500}, ...}
@app.get("/transactions/history")
def get_transactions_history(db: Session = Depends(get_db)):
    # Get transactions for the last six full months and current month
    six_months_ago = pd.to_datetime("today") - pd.DateOffset(months=6)
    six_months_ago = six_months_ago.replace(day=1)

    transactions = db.query(Transaction).filter(Transaction.date >= six_months_ago, Transaction.category != 'Transfer').all()

    history = {}
    
    for transaction in transactions:
        year_month = transaction.date.strftime("%B %Y")
        if year_month not in history:
            history[year_month] = {"income": 0, "expenses": 0}
        if transaction.section == 'Income':
            history[year_month]["income"] += transaction.amount
        else:
            history[year_month]["expenses"] += transaction.amount

    # reverse the order of the history
    history = dict(reversed(list(history.items())))

    return history

# Get range of year-months for transactions
@app.get("/transactions/range")
def get_transactions_range(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    months = set()
    for transaction in transactions:
        year_month = transaction.date.strftime("%Y-%m")
        months.add(year_month)
    return sorted(list(months), reverse=True)

# Add sections to transactions based on categories
@app.post("/add-sections/")
async def add_sections(db: Session = Depends(get_db)):
    """Add sections to transactions based on categories"""

    logging.info("Adding sections to transactions...")
    transactions = db.query(Transaction).all()

    for transaction in transactions:
        category = transaction.category
        section = db.query(Category).filter(Category.category == category).first()
        if section:
            transaction.section = section.section

    db.commit()
    logging.info("Sections added to transactions.")
    return {"message": "Sections added to transactions."}

# categorize transactions
@app.post("/categorize-transactions/")
async def categorize_transactions(db: Session = Depends(get_db)):
    """Categorize transactions"""

    logging.info("Categorizing transactions...")
    transactions = db.query(Transaction).filter(Transaction.is_indexed == 0).all()

    for transaction in transactions:
        description = transaction.description
        searcher = Searcher()
        es_result = searcher.execute_search(field="description",
                                            shoulds=[description])["hits"]["hits"]

        category = es_result[0]["_source"]["annotated_category"] if es_result else "Unknown"
        transaction.category = category

    db.commit()
    logging.info("Categorization complete.")
    return {"message": "Transactions categorized."}

# Add data to elasticsearch
@app.post("/add-data/")
async def add_data(file: Annotated[UploadFile, Form(...)]):
    """Add data to Elasticsearch"""

    logging.info("Adding data to Elasticsearch...")
    df = pd.read_excel(io.BytesIO(file.file.read()))

    es_uploader = Uploader()

    # Upload all transactions to Elasticsearch
    es_uploader.post_df(df[['description','annotated_category']])

    logging.info("Data added to Elasticsearch.")
    return {"message": "Data added to Elasticsearch."}

# Get categories from Elasticsearch for a given description
@app.post("/get-categories/")
async def get_categories(description_request: DescriptionRequest):
    """Get categories from Elasticsearch for a given description"""

    description = description_request.description
    logging.info(f"Getting categories for description: {description}")
    searcher = Searcher()
    es_result = searcher.execute_search(field="description",
                                 shoulds=[description])["hits"]["hits"]

    category = es_result[0]["_source"]["annotated_category"] if es_result else "Unknown"
    logging.info(f"Category found: {category}")
    return {"category": category}

# Delete transaction
@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction"""

    logging.info(f"Deleting transaction {transaction_id}...")
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if transaction:
        db.delete(transaction)
        db.commit()
        logging.info(f"Transaction {transaction_id} deleted.")
        return get_transactions(db)
    else:
        raise HTTPException(status_code=404, detail="Transaction not found.")