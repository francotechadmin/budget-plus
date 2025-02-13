# app/auth.py

import json
import requests
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import JWTError

AUTH0_DOMAIN = "dev-gqc2uqr58a2eqikr.us.auth0.com"  # e.g., "your-tenant.auth0.com"
API_AUDIENCE = "http://localhost:8000"   # e.g., "https://your-api/"
ALGORITHMS = ["RS256"]

# Dependency for extracting the token from the Authorization header
http_bearer = HTTPBearer()

def get_token_auth_header(auth: HTTPAuthorizationCredentials = Security(http_bearer)) -> str:
    """
    Extracts and returns the token from the Authorization header.
    """
    return auth.credentials

def verify_jwt(token: str) -> dict:
    """
    Verify the JWT token using Auth0's public keys.
    """
    jsonurl = requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json", verify=False)
    jwks = jsonurl.json()
    unverified_header = jwt.get_unverified_header(token)
    
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
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
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

    # verify the token first
    verify_jwt(token)

    user_info_url = f"https://{AUTH0_DOMAIN}/userinfo"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(user_info_url, headers=headers, verify=False)
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")
    return response.json()