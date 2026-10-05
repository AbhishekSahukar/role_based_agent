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


def _unauthorized(reason: str) -> HTTPException:
    log.warning("auth rejected (401): %s", reason)
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _forbidden(reason: str) -> HTTPException:
    log.warning("auth rejected (403): %s", reason)
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied",
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> CurrentUser:
    # 1. A bearer token must be present.
    if creds is None or not creds.credentials:
        raise _unauthorized("no bearer token")

    token = creds.credentials

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
        raise _unauthorized(f"{type(e).__name__}: {e}")

    # 8. The delegated scope must be present.
    scopes = claims.get("scp", "").split()
    if config.REQUIRED_SCOPE not in scopes:
        raise _forbidden(f"required scope missing, scp={scopes}")

    # 9. Identity and roles come only from the validated claims.
    oid = claims.get("oid")
    if not oid:
        raise _unauthorized("token has no oid")

    name = claims.get("name") or claims.get("preferred_username") or "unknown"
    roles = claims.get("roles", [])

    # 10. No app role assigned -> refuse, even if Entra issued the token.
    if not roles:
        raise _forbidden(f"no app role assigned, oid={oid} name={name}")

    # 11. Labelled log line: proves where the role came from.
    log.info("auth ok oid=%s name=%s roles=%s scp=%s", oid, name, roles, scopes)

    return CurrentUser(oid=oid, name=name, roles=roles)