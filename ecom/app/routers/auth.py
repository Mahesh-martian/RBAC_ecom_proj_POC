"""
Authentication API endpoints.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import APIRouter, HTTPException, Request, status

from app.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
)
from app.services.auth import AuthService
from app.dependencies import CurrentUserDep, DBSessionDep

router = APIRouter(prefix="/auth", tags=["authentication"])

_auth_limit_lock = Lock()
_auth_events: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _enforce_auth_rate_limit(request: Request, bucket: str, limit: int, period_seconds: int) -> None:
    key = f"{bucket}:{_client_ip(request)}"
    now = time.time()

    with _auth_limit_lock:
        events = _auth_events[key]
        cutoff = now - period_seconds
        while events and events[0] < cutoff:
            events.popleft()
        if len(events) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication attempts. Please retry later.",
            )
        events.append(now)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user"
)
async def register(
    request_context: Request,
    request: UserRegisterRequest,
    session: DBSessionDep,
) -> UserResponse:
    """
    Register a new user account.
    
    - **email**: Unique email address
    - **password**: Min 12 chars, 1 uppercase, 1 digit
    - **name**: Full name
    - **phone**: Optional phone number
    """
    _enforce_auth_rate_limit(request_context, bucket="register", limit=5, period_seconds=60)

    try:
        user = await AuthService.register_user(request, session)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user"
)
async def login(
    request_context: Request,
    request: UserLoginRequest,
    session: DBSessionDep,
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.
    
    Returns:
    - **access_token**: JWT token for authenticated requests (expires in 24 hours)
    - **refresh_token**: Token to refresh access token (expires in 30 days)
    """
    _enforce_auth_rate_limit(request_context, bucket="login", limit=10, period_seconds=60)

    return await AuthService.login_user(request, session)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token"
)
async def refresh_token(
    request_context: Request,
    refresh_token: str,
    session: DBSessionDep,
) -> TokenResponse:
    """
    Create new access token from refresh token.
    """
    _enforce_auth_rate_limit(request_context, bucket="refresh", limit=20, period_seconds=60)

    return await AuthService.refresh_access_token(refresh_token, session)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user"
)
async def get_me(
    current_user: CurrentUserDep,
) -> UserResponse:
    """
    Get current authenticated user profile.
    """
    return UserResponse.model_validate(current_user)
