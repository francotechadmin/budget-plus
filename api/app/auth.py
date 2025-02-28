import time
import json
import logging
import requests
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import JWTError
import urllib3
import os

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")  # e.g., "your-tenant.auth0.com"
API_AUDIENCE = os.getenv("API_AUDIENCE") # e.g., "https://your-api-identifier"
ALGORITHMS = ["RS256"]

# Configure logging
logger = logging.getLogger("auth_logger")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Cache variables for JWKS keys
JWKS_CACHE = None
JWKS_CACHE_EXPIRES_AT = 0
JWKS_CACHE_TIMEOUT = 3600  # seconds, adjust as needed (e.g., 1 hour)

# Dependency for extracting the token from the Authorization header
http_bearer = HTTPBearer()

def get_token_auth_header(auth: HTTPAuthorizationCredentials = Security(http_bearer)) -> str:
    """
    Extracts and returns the token from the Authorization header.
    """
    token = auth.credentials
    logger.debug("Extracted token from Authorization header.")
    return token

def get_jwks() -> dict:
    """
    Retrieves JWKS keys from Auth0, using a cached version if available and not expired.
    """
    global JWKS_CACHE, JWKS_CACHE_EXPIRES_AT
    current_time = time.time()
    if JWKS_CACHE is None or current_time > JWKS_CACHE_EXPIRES_AT:
        logger.info("JWKS cache expired or not found. Fetching new JWKS keys.")
        logger.debug(f"URL: https://{AUTH0_DOMAIN}/.well-known/jwks.json")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json", verify=False)
        if response.status_code != 200:
            logger.error(f"Failed to fetch JWKS keys. Status code: {response.status_code}")
            raise HTTPException(status_code=500, detail="Unable to fetch JWKS keys")
        JWKS_CACHE = response.json()
        JWKS_CACHE_EXPIRES_AT = current_time + JWKS_CACHE_TIMEOUT
        logger.info("JWKS keys fetched and cache updated.")
    else:
        logger.debug("Using cached JWKS keys.")
    return JWKS_CACHE

def verify_jwt(token: str) -> dict:
    """
    Verify the JWT token using Auth0's public keys.
    """
    logger.debug("Verifying JWT token.")
    jwks = get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
        logger.debug(f"Unverified JWT header: {unverified_header}")
    except JWTError as e:
        logger.error(f"Error decoding token header: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token header")
    
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header.get("kid"):
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            logger.debug("Matching JWKS key found.")
            break

    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            logger.info("JWT token successfully verified.")
            return payload
        except JWTError as e:
            logger.error(f"JWT verification error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        logger.error("Unable to find appropriate JWKS key for token.")
        raise HTTPException(status_code=401, detail="Unable to find appropriate key")

def get_current_user(token: str = Depends(get_token_auth_header)) -> dict:
    """
    Dependency that returns the decoded JWT payload.
    """
    return verify_jwt(token)

def get_user_info(token: str = Depends(get_token_auth_header)) -> dict:
    """
    Fetch user information from Auth0.
    """
    # Verify the token first
    verify_jwt(token)
    logger.debug("Fetching user info from Auth0.")

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    user_info_url = f"https://{AUTH0_DOMAIN}/userinfo"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(user_info_url, headers=headers, verify=False)
    if response.status_code != 200:
        logger.error(f"Failed to fetch user info. Status code: {response.status_code}")
        raise HTTPException(status_code=401, detail="Invalid token")
    logger.info("User info successfully retrieved.")
    return response.json()
