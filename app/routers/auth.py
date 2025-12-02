# app/routers/auth.py - COMPLETE VERSION
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime
import os
import logging

from app.database import get_session
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    GoogleAuthRequest,
)
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
)
from app.utils.google_oauth import get_google_oauth_flow, verify_google_token

router = APIRouter()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")

logger = logging.getLogger(__name__)


# Add this class at the top of auth.py
class LoginForm(BaseModel):
    username: str
    password: str


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Register a new user with email and password."""

    # Check if user already exists
    result = await session.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hashed_password,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: LoginForm,  # Use custom form instead of OAuth2PasswordRequestForm
    session: AsyncSession = Depends(get_session),
):
    """Login with email and password (OAuth2 compatible), returns JWT token."""

    # Find user by email (OAuth2 uses 'username' field)
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await session.commit()

    # Create access token
    access_token = create_access_token(data={"user_id": user.id, "email": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.post("/login/json", response_model=Token)
async def login_json(
    credentials: UserLogin, session: AsyncSession = Depends(get_session)
):
    """Alternative login endpoint that accepts JSON (for frontend forms)."""

    result = await session.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user.last_login = datetime.utcnow()
    await session.commit()

    access_token = create_access_token(data={"user_id": user.id, "email": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user information."""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout endpoint (token invalidation handled client-side)."""
    return {"message": "Successfully logged out"}


@router.get("/google/login")
async def google_login():
    """Initiate Google OAuth flow - redirects to Google login page."""
    flow = get_google_oauth_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )

    return {"authorization_url": authorization_url, "state": state}


@router.get("/google/callback")
async def google_callback(code: str, session: AsyncSession = Depends(get_session)):
    """Handle Google OAuth callback."""

    logger.info(f"Google callback received with code: {code[:20]}...")

    try:
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        }

        logger.info(
            f"Exchanging code for token with redirect_uri: {os.getenv('GOOGLE_REDIRECT_URI')}"
        )

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)

            logger.info(f"Token response status: {token_response.status_code}")
            logger.info(f"Token response body: {token_response.text}")

            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code: {token_response.text}",
                )

            tokens = token_response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")

            logger.info("Token exchange successful")

            # Get user info
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient() as client:
                userinfo_response = await client.get(userinfo_url, headers=headers)

                logger.info(
                    f"Userinfo response status: {userinfo_response.status_code}"
                )

                if userinfo_response.status_code != 200:
                    logger.error(f"Failed to get user info: {userinfo_response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to get user info: {userinfo_response.text}",
                    )

                user_info = userinfo_response.json()
                logger.info(f"User info retrieved: {user_info.get('email')}")

        # Check if user exists
        result = await session.execute(
            select(User).where(User.google_id == user_info["id"])
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                email=user_info["email"],
                full_name=user_info.get("name", ""),
                google_id=user_info["id"],
                google_refresh_token=refresh_token,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Created new user: {user.email}")
        else:
            # Update refresh token
            user.google_refresh_token = refresh_token
            user.last_login = func.now()
            await session.commit()
            logger.info(f"Updated existing user: {user.email}")

        # Create access token
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email}
        )

        # Redirect to frontend with token
        frontend_url = f"{FRONTEND_URL}/auth_callback?token={access_token}"
        return RedirectResponse(url=frontend_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Google: {str(e)}",
        )


@router.post("/google/token", response_model=Token)
async def google_token_exchange(
    auth_request: GoogleAuthRequest, session: AsyncSession = Depends(get_session)
):
    """
    Alternative endpoint for frontend to exchange Google auth code for JWT.
    Better for SPA/React/htmx apps that handle OAuth popup.
    """

    flow = get_google_oauth_flow()

    try:
        flow.fetch_token(code=auth_request.code)
        credentials = flow.credentials
        idinfo = verify_google_token(credentials.id_token)

        google_id = idinfo["sub"]
        email = idinfo["email"]
        full_name = idinfo.get("name", email.split("@")[0])

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Google: {str(e)}",
        )

    # Find or create user (same logic as callback)
    result = await session.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.google_id = google_id
            user.google_refresh_token = credentials.refresh_token
        else:
            user = User(
                email=email,
                full_name=full_name,
                google_id=google_id,
                google_refresh_token=credentials.refresh_token,
            )
            session.add(user)
    else:
        if credentials.refresh_token:
            user.google_refresh_token = credentials.refresh_token

    user.last_login = datetime.utcnow()
    await session.commit()
    await session.refresh(user)

    access_token = create_access_token(data={"user_id": user.id, "email": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }
