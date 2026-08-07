from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.auth.models import Role, User
from app.auth.permissions import tool_allowed
from app.auth.security import decode_access_token
from app.core.rate_limiter import check_rate_limit

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise credentials_error

    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise credentials_error

    return User(username=username, role=Role(role))


def require_permission(tool: str):
    async def _check(user: User = Depends(get_current_user)) -> User:
        if not tool_allowed(tool, user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' is not permitted to use tool '{tool}'",
            )
        return user

    return _check


async def enforce_rate_limit(user: User = Depends(get_current_user)) -> User:
    # FastAPI caches get_current_user's result per request, so this doesn't
    # re-decode the token if another dependency (e.g. require_permission)
    # already resolved it in the same request.
    allowed, retry_after = await check_rate_limit(user.username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down and try again shortly.",
            headers={"Retry-After": str(max(1, int(retry_after) + 1))},
        )
    return user
