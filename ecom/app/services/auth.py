"""
Authentication service for user management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt
import logging
from fastapi import HTTPException, status

from app.models import User
from app.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.dependencies import JWTHandler

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify plain password against hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    
    @staticmethod
    async def register_user(
        request: UserRegisterRequest,
        session: AsyncSession
    ) -> User:
        """
        Register a new user.
        
        Args:
            request: Registration request data
            session: Database session
            
        Returns:
            Created User object
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        stmt = select(User).where(User.email == request.email.lower())
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = AuthService.hash_password(request.password)
        
        new_user = User(
            email=request.email.lower(),
            password_hash=hashed_password,
            name=request.name,
            phone=request.phone,
            email_verified=False,  # In production, send verification email
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        logger.info(f"New user registered: {new_user.email}")
        return new_user
    
    @staticmethod
    async def login_user(
        request: UserLoginRequest,
        session: AsyncSession
    ) -> TokenResponse:
        """
        Authenticate user and return tokens.
        
        Args:
            request: Login request data
            session: Database session
            
        Returns:
            TokenResponse with access and refresh tokens
            
        Raises:
            HTTPException: If credentials invalid
        """
        # Find user by email
        stmt = select(User).where(User.email == request.email.lower())
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not AuthService.verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        await session.commit()
        
        # Create tokens
        access_token, access_expires = JWTHandler.create_token(user.id, token_type="access")
        refresh_token, refresh_expires = JWTHandler.create_token(user.id, token_type="refresh")
        
        logger.info(f"User logged in: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=access_expires
        )
    
    @staticmethod
    async def refresh_access_token(
        refresh_token: str,
        session: AsyncSession
    ) -> TokenResponse:
        """
        Create new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            session: Database session
            
        Returns:
            TokenResponse with new access token
            
        Raises:
            HTTPException: If refresh token invalid
        """
        # Verify refresh token
        payload = JWTHandler.verify_token(refresh_token, token_type="refresh")
        user_id = int(payload.get("sub"))
        
        # Verify user still exists and is active
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token, access_expires = JWTHandler.create_token(user.id, token_type="access")
        
        return TokenResponse(
            access_token=access_token,
            expires_in=access_expires
        )
