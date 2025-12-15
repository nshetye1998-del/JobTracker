from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import httpx
from libs.core.db import User
from src.database import get_db
from libs.core.logger import configure_logger

logger = configure_logger("auth")

async def verify_google_token(token: str) -> dict:
    """Verify Google OAuth token and return user info"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {token}'}
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Google token verification failed: {e}")
        return None

async def verify_microsoft_token(token: str) -> dict:
    """Verify Microsoft OAuth token and return user info"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={'Authorization': f'Bearer {token}'}
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Microsoft token verification failed: {e}")
        return None

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from OAuth token.
    Returns None if no token provided (allows anonymous access).
    Raises HTTPException if token is invalid.
    """
    if not authorization:
        return None
    
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split('Bearer ')[1]
    
    # Try Google first
    user_info = await verify_google_token(token)
    provider = 'google'
    
    # If Google fails, try Microsoft
    if not user_info:
        user_info = await verify_microsoft_token(token)
        provider = 'microsoft'
    
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Extract user data based on provider
    if provider == 'google':
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0] if email else None)
        oauth_id = user_info.get('id')
    else:  # microsoft
        email = user_info.get('mail') or user_info.get('userPrincipalName')
        name = user_info.get('displayName', email.split('@')[0] if email else None)
        oauth_id = user_info.get('id')
    
    if not email or not oauth_id:
        raise HTTPException(status_code=401, detail="Invalid user data from OAuth provider")
    
    # Get or create user in database
    user = db.query(User).filter(User.oauth_id == oauth_id).first()
    
    if not user:
        user = User(
            email=email,
            name=name,
            oauth_provider=provider,
            oauth_id=oauth_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user: {email} via {provider}")
    else:
        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.commit()
    
    return user

async def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authentication - raises 401 if no user"""
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return current_user
