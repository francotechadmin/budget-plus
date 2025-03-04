# app/transaction_categorization/preprocessing.py

import re

def preprocess(text: str) -> str:
    """Basic text preprocessing: lowercasing, stripping whitespace, and removing punctuation."""
    text = text.lower().strip()
    # Remove punctuation (you can expand this with more robust cleaning)
    text = re.sub(r'[^\w\s]', '', text)
    return text
