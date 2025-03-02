# app/transaction_categorization/model.py

import joblib
from .preprocessing import preprocess
import os

# Define paths to the model artifacts
MODEL_PATH = os.path.join(os.path.dirname(__file__), "transaction_categorizer.pkl")
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "tfidf_vectorizer.pkl")

# Load the model and vectorizer at module level
model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

def predict_category(description: str) -> str:
    """
    Preprocess the transaction description, transform it using the vectorizer,
    and return the predicted category.
    """
    processed_text = preprocess(description)
    text_vect = vectorizer.transform([processed_text])
    prediction = model.predict(text_vect)[0]
    return prediction

def predict_category_with_confidence(description: str):
    processed_text = preprocess(description)
    text_vect = vectorizer.transform([processed_text])
    prediction = model.predict(text_vect)[0]
    confidence = max(model.predict_proba(text_vect)[0])
    is_uncertain = confidence < 0.05  # Define your threshold here
    return prediction, confidence, is_uncertain
