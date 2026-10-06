import logging
from dataclasses import dataclass, field

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app import config

log = logging.getLogger("askhr.auth")

# auto_error=False: we decide between 401 and 403 ourselves.
bearer = HTTPBearer(auto_error=False)

# Fetches Entra's public signing keys from the JWKS endpoint and caches them.
jwks_client = PyJWKClient(config.JWKS_URL)


@dataclass
class CurrentUser:
    oid: str
    name: str
    roles: list[str] = field(default_factory=list)
    # The validated token itself: needed to call our MCP server and for OBO.
    # repr=False keeps it out of any accidental print or log of the object.
    access_token: str = field(default="", repr=False)


class AuthError(Exception):
    def __init__(self, status_code: int, reason: str):
        super().__init__(reason)
        self.status_code = status_code
        self.reason = reason


def validate_token(token: str) -> CurrentUser:
    """All checks in one place. Used by FastAPI routes AND the MCP server."""
    # 1. A token must be present.
    if not token:
        raise AuthError(401, "no bearer token")

    # 2-7. Signature, algorithm, issuer, audience, expiry, not-before.
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=config.API_CLIENT_ID,
            issuer=config.ISSUER,
            options={"require": ["exp", "nbf", "iss", "aud"]},
        )
    except jwt.PyJWTError as e:
        raise AuthError(401, f"{type(e).__name__}: {e}")

    # 8. The delegated scope must be present.
    scopes = claims.get("scp", "").split()
    if config.REQUIRED_SCOPE not in scopes:
        raise AuthError(403, f"required scope missing, scp={scopes}")

    # 9. Identity and roles come only from the validated claims.
    oid = claims.get("oid")
    if not oid:
        raise AuthError(401, "token has no oid")

    name = claims.get("name") or claims.get("preferred_username") or "unknown"
    roles = claims.get("roles", [])

    # 10. No app role assigned -> refuse, even if Entra issued the token.
    if not roles:
        raise AuthError(403, f"no app role assigned, oid={oid} name={name}")

    # 11. Labelled log line: proves where the role came from.
    log.info("auth ok oid=%s name=%s roles=%s scp=%s", oid, name, roles, scopes)
    return CurrentUser(oid=oid, name=name, roles=roles, access_token=token)


def _to_http(e: AuthError) -> HTTPException:
    log.warning("auth rejected (%s): %s", e.status_code, e.reason)
    if e.status_code == 401:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> CurrentUser:
    """FastAPI dependency for /whoami and /chat."""
    try:
        return validate_token(creds.credentials if creds else "")
    except AuthError as e:
        raise _to_http(e)