import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import mplcursors

def ingest_bank_csv(file_path):
    df = pd.read_csv(file_path, usecols=['Details', 'Posting Date', 'Description', 'Amount', 'Type', 'Balance', 'Check or Slip #'])
    return df

def ingest_credit_csv(file_path):
    df = pd.read_csv(file_path, usecols=['Transaction Date', 'Post Date', 'Description', 'Category', 'Type', 'Amount', 'Memo'])
    return df

def create_db(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # drop tables if they exist
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
    for index, row in df.iterrows():
        cursor.execute('''
            INSERT INTO bank_transactions (
                details, posting_date, description, amount, type, balance, check_or_slip
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (row['Details'], row['Posting Date'], row['Description'], row['Amount'], row['Type'], row.get('Balance', None), row.get('Check or Slip #', None)))
    conn.commit()

def insert_credit_transactions(conn, df):
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute('''
            INSERT INTO credit_transactions (
                transaction_date, post_date, description, category, type, amount, memo
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (row['Transaction Date'], row['Post Date'], row['Description'], row['Category'], row['Type'], row['Amount'], row.get('Memo', None)))
    conn.commit()

def visualize_data(conn):
    # Bank Transactions
    bank_df = pd.read_sql_query("SELECT * FROM bank_transactions", conn)

    # Credit Transactions
    credit_df = pd.read_sql_query("SELECT * FROM credit_transactions", conn)

    # Visualization: transactions by category pie chart (Credit Transactions)
    credit_df['category'] = credit_df['category'].fillna('Unknown')
    fig, ax = plt.subplots()
    credit_df['category'].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
    plt.title('Credit Transactions by Category')
    mplcursors.cursor(ax, hover=True).connect("add", lambda sel: sel.annotation.set_text(f"Category: {credit_df['category'].value_counts().index[sel.index]}\nCount: {credit_df['category'].value_counts().iloc[sel.index]}"))
    plt.show()

    # Combined Visualization: Money In vs Money Out per Month for the last 6 months (Bank Transactions)
    bank_df['posting_date'] = pd.to_datetime(bank_df['posting_date'])
    bank_df['month'] = bank_df['posting_date'].dt.month
    bank_df['year'] = bank_df['posting_date'].dt.year
    bank_df['money_in'] = bank_df['amount'].apply(lambda x: x if x > 0 else 0)
    bank_df['money_out'] = bank_df['amount'].apply(lambda x: x if x < 0 else 0)
    grouped_bank_df = bank_df.groupby(['year', 'month']).agg({'money_in': 'sum', 'money_out': 'sum'}).reset_index()
    grouped_bank_df['money_in'] = grouped_bank_df['money_in'] * -1
    fig, ax = plt.subplots()
    grouped_bank_df.plot(x='month', y=['money_in', 'money_out'], kind='bar', stacked=True, ax=ax)
    plt.xlabel('Month')
    plt.ylabel('Amount')
    plt.title('Bank Money In vs Money Out per Month')
    mplcursors.cursor(ax, hover=True).connect("add", lambda sel: sel.annotation.set_text(f"Month: {grouped_bank_df['month'].iloc[sel.index]}\nMoney In: {grouped_bank_df['money_in'].iloc[sel.index]:.2f}\nMoney Out: {grouped_bank_df['money_out'].iloc[sel.index]:.2f}"))
    plt.show()

def show_data(conn):
    bank_df = pd.read_sql_query("SELECT * FROM bank_transactions", conn)
    credit_df = pd.read_sql_query("SELECT * FROM credit_transactions", conn)
    print("Bank Transactions:\n", bank_df)
    print("Credit Transactions:\n", credit_df)

# def main():
#     bank_file_path = 'Python/budget/Chase6170_Activity_20240716.CSV'
#     credit_file_path = 'Python/budget/Chase8770_Activity20220716_20240716_20240717.CSV'
#     savings_file_path = 'Python/budget/Chase2977_Activity_20240716.CSV'
#     db_name = 'transactions.db'
    
#     # Step 1: Ingest CSV Data
#     bank_df = ingest_bank_csv(bank_file_path)
#     savings_df = ingest_bank_csv(savings_file_path)
#     credit_df = ingest_credit_csv(credit_file_path)
    
#     # Step 2: Create SQLite Database and Tables
#     conn = create_db(db_name)
    
#     # Step 3: Insert Transactions into Database
#     insert_bank_transactions(conn, bank_df)
#     insert_bank_transactions(conn, savings_df)
#     insert_credit_transactions(conn, credit_df)
    
#     # Step 4: Visualize Data
#     visualize_data(conn)

#     # Step 5: Show Data
#     show_data(conn)
    
#     conn.close()

# if __name__ == "__main__":
#     main()
