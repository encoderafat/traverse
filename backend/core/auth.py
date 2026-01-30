from functools import lru_cache
import os
import requests
from typing import Optional
from uuid import UUID

from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SUPABASE_URL = os.getenv("SUPABASE_URL")
JWT_AUDIENCE = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")



bearer_scheme = HTTPBearer(auto_error=False)

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL not set")

if not SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_ANON_KEY not set")

JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_jwks():
    try:
        res = requests.get(
            JWKS_URL,
            headers={
                "apikey": SUPABASE_ANON_KEY,
            },
            timeout=5,
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch JWKS: {e}")



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

def get_public_key(token: str):
    jwks = get_jwks()
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")

    if not kid:
        raise HTTPException(status_code=401, detail="Missing kid in token")

    for key in jwks["keys"]:
        if key["kid"] == kid:
            return key

    raise HTTPException(status_code=401, detail="Public key not found")


def verify_supabase_jwt(token: str) -> AuthenticatedUser:
    try:
        public_key = get_public_key(token)
        if "alg" not in public_key:
            raise HTTPException(status_code=401, detail="Missing alg in public key")

        payload = jwt.decode(
            token,
            public_key,
            algorithms=[public_key["alg"]],
            audience=JWT_AUDIENCE,
            options={"verify_iss": False},  # Supabase does not require issuer
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing sub claim")

    email = payload.get("email")
    role = payload.get("role") or payload.get("app_metadata", {}).get("role")

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
