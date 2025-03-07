import pytest
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import os
import sys
from app.categorization.model import preprocess

# We need to mock the joblib.load calls before importing the module
# This prevents actual file loading during tests
@pytest.fixture(autouse=True)
def mock_model_loading():
    """Mock the model and vectorizer loading to avoid file dependencies."""
    # Create mock model
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array(["Groceries"])
    mock_model.predict_proba.return_value = np.array([[0.8, 0.1, 0.1]])
    
    # Create mock vectorizer
    mock_vectorizer = MagicMock()
    mock_vectorizer.transform.return_value = "transformed_text"
    
    # Patch joblib.load to return our mocks
    with patch("joblib.load") as mock_load:
        # Configure mock_load to return different values based on the argument
        def side_effect(path):
            if "transaction_categorizer.pkl" in path:
                return mock_model
            elif "tfidf_vectorizer.pkl" in path:
                return mock_vectorizer
            return None
        
        mock_load.side_effect = side_effect
        
        # Patch os.path.exists to return True for our model files
        with patch("os.path.exists", return_value=True):
            # Now import the module after patching
            import app.categorization.model
            
            # Force reload if it was already imported
            import importlib
            importlib.reload(app.categorization.model)
            
            yield mock_model, mock_vectorizer

class TestTransactionCategorization:
    def test_preprocessing_integration(self):
        """Test that preprocessing function is properly integrated."""
        from app.categorization.model import preprocess
        
        # Test with a sample description
        description = "WALMART GROCERY STORE 12345"
        processed = preprocess(description)
        
        # Check basic preprocessing was applied
        assert processed == processed.lower()  # Should be lowercase
        assert "walmart" in processed
        assert "grocery" in processed
        assert "store" in processed
        
        # Numbers should be removed or replaced
        assert "12345" not in processed

    def test_predict_category(self, mock_model_loading):
        """Test the predict_category function."""
        mock_model, mock_vectorizer = mock_model_loading
        from app.categorization.model import predict_category
        
        # Test prediction
        result = predict_category("Test Transaction")
        
        # Check the preprocessing and transformation flow
        mock_vectorizer.transform.assert_called_once()
        mock_model.predict.assert_called_once()
        
        # Check the result
        assert result == "Groceries"  # This is from our mock model

    def test_predict_category_with_confidence(self, mock_model_loading):
        """Test the predict_category_with_confidence function."""
        mock_model, mock_vectorizer = mock_model_loading
        from app.categorization.model import predict_category_with_confidence
        
        # Test prediction with confidence
        category, confidence, is_uncertain = predict_category_with_confidence("Test Transaction")
        
        # Check the preprocessing and transformation flow
        mock_vectorizer.transform.assert_called_once()
        mock_model.predict.assert_called_once()
        mock_model.predict_proba.assert_called_once()
        
        # Check the results
        assert category == "Groceries"  # From our mock model
        assert confidence == 0.8  # From our mock predict_proba
        assert is_uncertain is False  # 0.8 is above the uncertainty threshold (0.05)

    def test_uncertain_prediction(self, mock_model_loading):
        """Test prediction with low confidence."""
        mock_model, mock_vectorizer = mock_model_loading
        from app.categorization.model import predict_category_with_confidence
        
        # Change the mock to return a low confidence value
        mock_model.predict_proba.return_value = np.array([[0.04, 0.03, 0.03]])  # Below 0.05 threshold
        
        # Test prediction with low confidence
        category, confidence, is_uncertain = predict_category_with_confidence("Ambiguous Transaction")
        
        # Check the results
        assert confidence == 0.04
        assert is_uncertain is True  # Below the uncertainty threshold

    def test_different_categories(self, mock_model_loading):
        """Test predicting different categories."""
        mock_model, mock_vectorizer = mock_model_loading
        from app.categorization.model import predict_category
        
        # Set the mock to return different categories for different calls
        mock_model.predict.side_effect = [
            np.array(["Groceries"]),
            np.array(["Dining"]),
            np.array(["Transportation"])
        ]
        
        # Make predictions with different descriptions
        result1 = predict_category("WALMART")
        result2 = predict_category("MCDONALD'S")
        result3 = predict_category("UBER RIDE")
        
        # Check the results
        assert result1 == "Groceries"
        assert result2 == "Dining"
        assert result3 == "Transportation"

    @patch("app.categorization.model.logger")
    def test_logging(self, mock_logger, mock_model_loading):
        """Test that predictions are properly logged."""
        from app.categorization.model import predict_category, predict_category_with_confidence
        
        # Test basic prediction logging
        predict_category("Test Transaction")
        mock_logger.info.assert_called_with("Predicted category: %s", "Groceries")
        
        # Reset mock
        mock_logger.reset_mock()
        
        # Test prediction with confidence logging
        predict_category_with_confidence("Test Transaction")
        
        # Check that all expected log entries are made
        log_calls = [call.args for call in mock_logger.info.call_args_list]
        assert any("Predicting category with confidence" in args[0] for args in log_calls)
        assert any("Predicted category: %s, Confidence: %f, Is uncertain: %s" in args[0] for args in log_calls)

    def test_error_handling(self, mock_model_loading):
        """Test that errors in the model are handled appropriately."""
        mock_model, mock_vectorizer = mock_model_loading
        from app.categorization.model import predict_category
        
        # Configure the mock to raise an exception
        mock_model.predict.side_effect = Exception("Model error")
        
        # Test that the exception propagates (you could change this if you want to handle it in the function)
        with pytest.raises(Exception) as exc_info:
            predict_category("Test Transaction")
        
        assert "Model error" in str(exc_info.value)
