"""
Dependency injection for FastAPI.
Handles authentication, authorization, and service provision.
"""

from typing import Optional, Annotated
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
import logging
from datetime import datetime, timedelta

from app.config import settings
from app.db import get_db_session
from app.models import User
from sqlalchemy import select

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class JWTHandler:
    """JWT token creation and validation."""
    
    @staticmethod
    def create_token(user_id: int, token_type: str = "access") -> tuple[str, int]:
        """
        Create JWT token.
        
        Args:
            user_id: User ID to encode
            token_type: 'access' or 'refresh'
            
        Returns:
            Tuple of (token, expires_in_seconds)
        """
        if token_type == "access":
            expires_in_seconds = settings.jwt_expiration_hours * 3600
        else:  # refresh
            expires_in_seconds = settings.jwt_refresh_expiration_days * 86400
        
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": datetime.utcnow().timestamp(),
            "exp": expires_at.timestamp(),
        }
        
        token = jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )
        
        return token, expires_in_seconds
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict:
        """
        Verify JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            Payload dict
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: Bearer token from Authorization header
        session: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials"
        )
    
    token = credentials.credentials
    
    # Verify token
    payload = JWTHandler.verify_token(token, token_type="access")
    user_id = int(payload.get("sub"))
    
    # Get user from database
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.
    For endpoints that allow both authenticated and guest access.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify they are admin.
    """
    # In a real app, check user.role or user.is_admin
    # For now, we'll check a custom field (you can add is_admin to User model)
    # This is a placeholder
    if not hasattr(current_user, "is_admin") or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


# Type aliases for cleaner dependency declarations
CurrentUserDep = Annotated[User, Depends(get_current_user)]
OptionalUserDep = Annotated[Optional[User], Depends(get_optional_user)]
AdminUserDep = Annotated[User, Depends(get_admin_user)]
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
