import logging

import msal

from app import config

log = logging.getLogger("askhr.obo")

_app: msal.ConfidentialClientApplication | None = None


class OboError(Exception):
    pass


def _client() -> msal.ConfidentialClientApplication:
    # One instance per process: MSAL caches OBO tokens per user assertion,
    # so repeated calls don't hit Entra every time.
    global _app
    if _app is None:
        _app = msal.ConfidentialClientApplication(
            client_id=config.API_CLIENT_ID,
            authority=config.AUTHORITY,
            client_credential=config.API_CLIENT_SECRET,
        )
    return _app


def graph_token_for(user_token: str) -> str:
    """Exchange the user's token for askhr-api into a Graph token for the same user.
    The incoming token MUST have our API as its audience (validated before this call).
    The returned Graph token is never parsed or logged: it belongs to Graph."""
    result = _client().acquire_token_on_behalf_of(
        user_assertion=user_token,
        scopes=config.GRAPH_SCOPES,
    )
    if "access_token" not in result:
        # e.g. invalid_grant (consent missing), interaction_required (Conditional Access)
        log.warning("obo failed error=%s codes=%s", result.get("error"), result.get("error_codes"))
        raise OboError(result.get("error", "unknown_error"))
    return result["access_token"]