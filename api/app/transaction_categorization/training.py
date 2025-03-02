# app/transaction_categorization/training.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib
import os

from preprocessing import preprocess
from default_rules import default_rules

def train_model():
    # Convert default rules into a DataFrame
    df = pd.DataFrame(default_rules)
    df['clean_desc'] = df['description'].apply(preprocess)

    # Define features and target variable
    X = df['clean_desc']
    y = df['category']

    # Vectorize the text using TF-IDF
    vectorizer = TfidfVectorizer()
    X_vect = vectorizer.fit_transform(X)

    # Use a simple train/test split (if the dataset is small, consider using all data for training)
    X_train, X_test, y_train, y_test = train_test_split(X_vect, y, test_size=0.2, random_state=42)

    # Train a Logistic Regression classifier
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Evaluate the model
    accuracy = model.score(X_test, y_test)
    print(f"Test Accuracy: {accuracy:.2f}")

    # Save the model and vectorizer for later use in the API
    current_dir = os.path.dirname(__file__)
    joblib.dump(model, os.path.join(current_dir, "transaction_categorizer.pkl"))
    joblib.dump(vectorizer, os.path.join(current_dir, "tfidf_vectorizer.pkl"))
    print("Model and vectorizer saved.")

if __name__ == "__main__":
    train_model()
