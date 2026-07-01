from functools import lru_cache
from typing import Annotated
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from config import settings
from database import get_db

_bearer = HTTPBearer()


@lru_cache(maxsize=1)
def _fetch_jwks() -> dict:
    resp = httpx.get(
        "https://api.clerk.com/v1/jwks",
        headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
    )
    resp.raise_for_status()
    return resp.json()


def verify_token(token: str) -> dict:
    """Validates a Clerk JWT and returns its claims."""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    jwks = _fetch_jwks()
    key_data = next((k for k in jwks["keys"] if k["kid"] == header.get("kid")), None)
    if not key_data:
        raise HTTPException(status_code=401, detail="Token signing key not found")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

    try:
        return jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_client_id(token: str) -> str:
    """Extracts the Clerk org_id string from a raw JWT."""
    claims = verify_token(token)
    org_id = claims.get("org_id")
    if not org_id:
        raise HTTPException(status_code=401, detail="Token missing org_id claim")
    return org_id


def get_authenticated_client(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(_bearer)],
    db: Session = Depends(get_db),
) -> UUID:
    """FastAPI dependency: validates Bearer token, returns internal client UUID."""
    org_id = get_current_client_id(credentials.credentials)

    from db.queries import get_client_by_org_id
    client = get_client_by_org_id(db, org_id)
    if not client:
        raise HTTPException(status_code=401, detail="Organization not registered")
    return client.id
