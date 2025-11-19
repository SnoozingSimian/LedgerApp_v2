# app/utils/google_oauth.py

import os
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from fastapi import HTTPException, status

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# OAuth 2.0 scopes
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def get_google_oauth_flow():
    """Create Google OAuth flow instance."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured",
        )

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )

    return flow


def verify_google_token(token: str) -> dict:
    """Verify Google ID token and return user info."""
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )

        # Verify token is for our app
        if idinfo["aud"] != GOOGLE_CLIENT_ID:
            raise ValueError("Invalid audience")

        return idinfo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}",
        )
