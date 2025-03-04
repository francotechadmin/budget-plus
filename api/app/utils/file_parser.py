# app/utils/file_parser.py
import io
import pandas as pd
from fastapi import HTTPException, UploadFile

async def parse_transactions_file(file: UploadFile) -> pd.DataFrame:
    file_ext = file.filename.lower()
    try:
        contents = await file.read()
        if file_ext.endswith(".csv"):
            contents_str = contents.decode('utf-8')
            cleaned_contents = "\n".join(line.rstrip(",") for line in contents_str.splitlines())
            df = pd.read_csv(io.StringIO(cleaned_contents))
        elif file_ext.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a CSV or Excel file.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    # Convert columns to lower case and rename as needed.
    df.columns = map(str.lower, df.columns)
    if 'transaction date' in df.columns:
        df.rename(columns={'transaction date': 'date'}, inplace=True)
    elif 'posting date' in df.columns:
        df.rename(columns={'posting date': 'date'}, inplace=True)
    if 'debit' in df.columns and 'credit' in df.columns:
        df['amount'] = 0 - df['debit'].fillna(0) - df['credit'].fillna(0)
        df.drop(columns=['debit', 'credit'], inplace=True)
    elif 'debit' in df.columns:
        df['amount'] = df['debit']
        df.drop(columns=['debit'], inplace=True)
    elif 'credit' in df.columns:
        df['amount'] = df['credit']
        df.drop(columns=['credit'], inplace=True)

    required_columns = {"date", "description", "amount"}
    if not required_columns.issubset(set(df.columns)):
        missing = required_columns - set(df.columns)
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing)}")
    try:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        if df['date'].isnull().any():
            raise HTTPException(status_code=400, detail="Invalid date format in file.")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid date format in file.")
    return df
