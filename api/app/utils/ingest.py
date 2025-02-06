import pandas as pd
import sqlite3

def ingest_bank_csv(file_path: str) -> pd.DataFrame:
    columns = ['Details', 'Posting Date', 'Description', 'Amount', 'Type', 'Balance', 'Check or Slip #']
    return pd.read_csv(file_path, usecols=columns)

def ingest_credit_csv(file_path: str) -> pd.DataFrame:
    columns = ['Transaction Date', 'Post Date', 'Description', 'Category', 'Type', 'Amount', 'Memo']
    return pd.read_csv(file_path, usecols=columns)

def create_sqlite_db(db_name: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS bank_transactions')
    cursor.execute('DROP TABLE IF EXISTS credit_transactions')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            details TEXT,
            posting_date TEXT,
            description TEXT,
            amount REAL,
            type TEXT,
            balance REAL,
            check_or_slip TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT,
            post_date TEXT,
            description TEXT,
            category TEXT,
            type TEXT,
            amount REAL,
            memo TEXT
        )
    ''')
    conn.commit()
    return conn

def insert_bank_transactions(conn, df):
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute('''
            INSERT INTO bank_transactions (
                details, posting_date, description, amount, type, balance, check_or_slip
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (row['Details'], row['Posting Date'], row['Description'], row['Amount'], row['Type'], row.get('Balance'), row.get('Check or Slip #')))
    conn.commit()

def insert_credit_transactions(conn, df):
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute('''
            INSERT INTO credit_transactions (
                transaction_date, post_date, description, category, type, amount, memo
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (row['Transaction Date'], row['Post Date'], row['Description'], row['Category'], row['Type'], row['Amount'], row.get('Memo')))
    conn.commit()
