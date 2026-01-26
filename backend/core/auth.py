import os
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
JWT_AUDIENCE = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
JWT_ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    def __init__(
        self,
        user_id: str,
        email: Optional[str] = None,
        role: Optional[str] = None,
        claims: Optional[dict] = None,
    ):
        self.id = user_id
        self.email = email
        self.role = role
        self.claims = claims or {}


def verify_supabase_jwt(token: str) -> AuthenticatedUser:
    if not JWT_SECRET:
        raise RuntimeError("SUPABASE_JWT_SECRET not set")

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing sub claim")

    email = payload.get("email")

    # Supabase roles usually live here
    role = (
        payload.get("role")
        or payload.get("app_metadata", {}).get("role")
    )

    return AuthenticatedUser(
        user_id=user_id,
        email=email,
        role=role,
        claims=payload,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return verify_supabase_jwt(credentials.credentials)


def get_current_user_id(
    user: AuthenticatedUser = Depends(get_current_user),
) -> str:
    return user.id

def require_role(*allowed_roles: str):
    def checker(user: AuthenticatedUser = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )
        return user

    return checker

def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Optional[AuthenticatedUser]:
    if not credentials:
        return None
    try:
        return verify_supabase_jwt(credentials.credentials)
    except HTTPException:
        return None

def enforce_ownership(
    *,
    resource_user_id: UUID,
    current_user: AuthenticatedUser,
):
    """
    Enforces that the current user owns the resource,
    unless they are an admin.
    """
    # Admins can do anything
    if current_user.role == "admin":
        return

    if UUID(current_user.id) != resource_user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not own this resource",
        )
