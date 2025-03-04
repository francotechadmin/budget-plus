# app/transaction_categorization/model.py

import joblib
from .preprocessing import preprocess
import os
from ..utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
# Define paths to the model artifacts
MODEL_PATH = os.path.join(os.path.dirname(__file__), "transaction_categorizer.pkl")
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "tfidf_vectorizer.pkl")

# Load the model and vectorizer at module level
logger.info("Loading model from %s", MODEL_PATH)
model = joblib.load(MODEL_PATH)
logger.info("Loading vectorizer from %s", VECTORIZER_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

def predict_category(description: str) -> str:
    """
    Preprocess the transaction description, transform it using the vectorizer,
    and return the predicted category.
    """
    logger.info("Predicting category for description: %s", description)
    processed_text = preprocess(description)
    text_vect = vectorizer.transform([processed_text])
    prediction = model.predict(text_vect)[0]
    logger.info("Predicted category: %s", prediction)
    return prediction

def predict_category_with_confidence(description: str):
    """
    Preprocess the transaction description, transform it using the vectorizer,
    and return the predicted category along with confidence and uncertainty.
    """
    logger.info("Predicting category with confidence for description: %s", description)
    processed_text = preprocess(description)
    text_vect = vectorizer.transform([processed_text])
    prediction = model.predict(text_vect)[0]
    confidence = max(model.predict_proba(text_vect)[0])
    is_uncertain = confidence < 0.05  # Define your threshold here
    logger.info("Predicted category: %s, Confidence: %f, Is uncertain: %s", prediction, confidence, is_uncertain)
    return prediction, confidence, is_uncertain
