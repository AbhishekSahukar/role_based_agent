import logging

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

from app import config

log = logging.getLogger("askhr.retrieval")

_client: SearchClient | None = None


def _get_client() -> SearchClient:
    # Created on first use, so importing this module needs no Azure access.
    # Locally DefaultAzureCredential uses your Azure CLI login; in Container Apps
    # (Phase 6) it uses the managed identity. No search key anywhere.
    global _client
    if _client is None:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        _client = SearchClient(config.SEARCH_ENDPOINT, config.SEARCH_INDEX, credential)
    return _client


def build_role_filter(roles: list[str]) -> str | None:
    """Security filter: only documents whose allowed_roles contain one of the
    caller's roles. `roles` must come from the validated token, never the prompt.

    Only known role names are used. They contain no quotes or commas, so the
    OData string can't be broken out of. Unknown values are dropped.
    Returns None when no known role remains: the caller must then search nothing.
    """
    allowed = sorted({r for r in roles if r in config.KNOWN_ROLES})
    if not allowed:
        return None
    joined = ",".join(allowed)
    return f"allowed_roles/any(r: search.in(r, '{joined}', ','))"


def search_policies(query: str, roles: list[str], oid: str) -> list[dict]:
    role_filter = build_role_filter(roles)
    if role_filter is None:
        # Fail closed: no usable role -> no documents, not "no filter".
        log.warning("search denied oid=%s roles=%s filter=none", oid, roles)
        return []

    results = _get_client().search(
        search_text=query,
        filter=role_filter,
        top=config.SEARCH_TOP,
        select=["id", "title", "content"],
    )
    docs = [{"id": r["id"], "title": r["title"], "content": r["content"]} for r in results]

    # The acceptance-test log line: who, which roles, which filter, which docs.
    log.info("search oid=%s roles=%s filter=%s hits=%s",
             oid, roles, role_filter, [d["id"] for d in docs])
    return docs