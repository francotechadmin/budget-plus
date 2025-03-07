import pytest
import time
import json
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from jose import jwt
from jose.exceptions import JWTError
import app.auth  # Import the module, not just the functions
from app.auth import (
    get_token_auth_header,
    verify_jwt,
    get_current_user,
    get_user_info
)

# Sample test data
MOCK_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Rfa2lkIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiZW1haWwiOiJqb2huQGV4YW1wbGUuY29tIiwiaWF0IjoxNTE2MjM5MDIyfQ.signature"
MOCK_JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "kid": "test_kid",
            "use": "sig",
            "n": "sample_n_value",
            "e": "AQAB"
        }
    ]
}
MOCK_USER_PAYLOAD = {
    "sub": "auth0|1234567890",
    "name": "John Doe",
    "email": "john@example.com",
    "email_verified": True
}
MOCK_HEADER = {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "test_kid"
}

class TestAuth:
    """Test suite for the authentication module."""

    def test_get_token_auth_header(self):
        """Test extracting token from auth header."""
        # Create a mock HTTPAuthorizationCredentials object
        mock_auth = MagicMock()
        mock_auth.credentials = MOCK_TOKEN
        
        # Test the function
        token = get_token_auth_header(mock_auth)
        assert token == MOCK_TOKEN

    @patch('app.auth.requests.get')
    def test_get_jwks_fresh(self, mock_get):
        """Test fetching JWKS when cache is expired or not found."""
        # Reset cache variables for testing
        app.auth.JWKS_CACHE = None
        app.auth.JWKS_CACHE_EXPIRES_AT = 0
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_JWKS
        mock_get.return_value = mock_response
        
        # Call function
        result = app.auth.get_jwks()
        
        # Verify function behavior
        assert result == MOCK_JWKS
        mock_get.assert_called_once()
        assert app.auth.JWKS_CACHE == MOCK_JWKS
        assert app.auth.JWKS_CACHE_EXPIRES_AT > time.time()

    @patch('app.auth.requests.get')
    def test_get_jwks_cached(self, mock_get):
        """Test using cached JWKS when available and not expired."""
        # Setup cache with non-expired value
        app.auth.JWKS_CACHE = MOCK_JWKS
        app.auth.JWKS_CACHE_EXPIRES_AT = time.time() + 3600  # 1 hour in the future
        
        # Call function
        result = app.auth.get_jwks()
        
        # Verify function behavior - request should not be made
        assert result == MOCK_JWKS
        mock_get.assert_not_called()

    @patch('app.auth.requests.get')
    def test_get_jwks_error(self, mock_get):
        """Test error handling when JWKS request fails."""
        # Reset cache variables for testing
        app.auth.JWKS_CACHE = None
        app.auth.JWKS_CACHE_EXPIRES_AT = 0
        
        # Setup mock response with error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        # Verify the function raises an exception
        with pytest.raises(HTTPException) as exc_info:
            app.auth.get_jwks()
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unable to fetch JWKS keys"
        mock_get.assert_called_once()

    def test_verify_jwt_invalid_header(self):
        """Test handling of invalid JWT header."""
        # Need to patch both functions since get_jwks is called before get_unverified_header
        with patch('app.auth.get_jwks') as mock_get_jwks:
            with patch('app.auth.jwt.get_unverified_header') as mock_get_header:
                # Setup mocks
                mock_get_jwks.return_value = MOCK_JWKS.copy()
                mock_get_header.side_effect = JWTError("Invalid header")
                
                # Verify the function raises an exception
                with pytest.raises(HTTPException) as exc_info:
                    verify_jwt(MOCK_TOKEN)
                
                assert exc_info.value.status_code == 401
                assert exc_info.value.detail == "Invalid token header"
                
                # Verify both functions were called in the expected order
                mock_get_jwks.assert_called_once()
                mock_get_header.assert_called_once()

    @patch('app.auth.jwt.get_unverified_header')
    @patch('app.auth.get_jwks')
    def test_verify_jwt_no_matching_key(self, mock_get_jwks, mock_get_header):
        """Test handling when no matching JWKS key is found."""
        # Setup mocks
        mock_get_header.return_value = {"kid": "different_kid"}
        mock_get_jwks.return_value = MOCK_JWKS.copy()
        
        # Verify the function raises an exception
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(MOCK_TOKEN)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Unable to find appropriate key"

    @patch('app.auth.jwt.get_unverified_header')
    @patch('app.auth.get_jwks')
    @patch('app.auth.jwt.decode')
    def test_verify_jwt_success(self, mock_decode, mock_get_jwks, mock_get_header):
        """Test successful JWT verification."""
        # Setup mocks
        mock_get_header.return_value = MOCK_HEADER.copy()
        mock_get_jwks.return_value = MOCK_JWKS.copy()
        mock_decode.return_value = MOCK_USER_PAYLOAD
        
        # Call function
        result = verify_jwt(MOCK_TOKEN)
        
        # Verify function behavior
        assert result == MOCK_USER_PAYLOAD
        mock_decode.assert_called_once()

    @patch('app.auth.jwt.get_unverified_header')
    @patch('app.auth.get_jwks')
    @patch('app.auth.jwt.decode')
    def test_verify_jwt_decode_error(self, mock_decode, mock_get_jwks, mock_get_header):
        """Test handling of JWT decode errors."""
        # Setup mocks
        mock_get_header.return_value = MOCK_HEADER.copy()
        mock_get_jwks.return_value = MOCK_JWKS.copy()
        mock_decode.side_effect = JWTError("Invalid signature")
        
        # Verify the function raises an exception
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(MOCK_TOKEN)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    @patch('app.auth.verify_jwt')
    def test_get_current_user(self, mock_verify_jwt):
        """Test the get_current_user dependency."""
        # Setup mock
        mock_verify_jwt.return_value = MOCK_USER_PAYLOAD
        
        # Call function
        result = get_current_user(MOCK_TOKEN)
        
        # Verify function behavior
        assert result == MOCK_USER_PAYLOAD
        mock_verify_jwt.assert_called_once_with(MOCK_TOKEN)

    @patch('app.auth.verify_jwt')
    @patch('app.auth.requests.get')
    def test_get_user_info_success(self, mock_get, mock_verify_jwt):
        """Test successful retrieval of user info."""
        # Setup mocks
        mock_verify_jwt.return_value = True  # Just need it to not raise an exception
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_USER_PAYLOAD
        mock_get.return_value = mock_response
        
        # Call function
        result = get_user_info(MOCK_TOKEN)
        
        # Verify function behavior
        assert result == MOCK_USER_PAYLOAD
        mock_verify_jwt.assert_called_once_with(MOCK_TOKEN)
        mock_get.assert_called_once()

    @patch('app.auth.verify_jwt')
    @patch('app.auth.requests.get')
    def test_get_user_info_error(self, mock_get, mock_verify_jwt):
        """Test handling of user info retrieval errors."""
        # Setup mocks
        mock_verify_jwt.return_value = True  # Just need it to not raise an exception
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        # Verify the function raises an exception
        with pytest.raises(HTTPException) as exc_info:
            get_user_info(MOCK_TOKEN)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"
        mock_verify_jwt.assert_called_once_with(MOCK_TOKEN)
        mock_get.assert_called_once()

    @patch('app.auth.verify_jwt')
    def test_get_user_info_verify_failure(self, mock_verify_jwt):
        """Test handling when initial token verification fails."""
        # Setup mock to raise exception
        mock_verify_jwt.side_effect = HTTPException(status_code=401, detail="Invalid token")
        
        # Verify the function raises an exception
        with pytest.raises(HTTPException) as exc_info:
            get_user_info(MOCK_TOKEN)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"
        mock_verify_jwt.assert_called_once_with(MOCK_TOKEN)