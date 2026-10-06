import asyncio
import itertools
import logging
import threading
from datetime import datetime, timezone

import httpx
from mcp.server.fastmcp import Context, FastMCP
from starlette.responses import JSONResponse

from app import config, obo
from app.auth import AuthError, CurrentUser, validate_token

log = logging.getLogger("askhr.mcp")

# stateless_http: every request is self-contained, so every request carries
# (and is checked for) the user's token. json_response: plain JSON, no SSE.
mcp = FastMCP("askhr-tools", stateless_http=True, json_response=True)

_tickets: list[dict] = []          # mock ticket store (in memory)
_ticket_ids = itertools.count(1001)
_lock = threading.Lock()


def _bearer_from(auth_header: str) -> str:
    return auth_header[7:] if auth_header.lower().startswith("bearer ") else ""


async def _caller(ctx: Context) -> CurrentUser:
    """Who is calling this tool? Decided ONLY by the validated bearer token,
    never by tool arguments. Raises AuthError if the token is not acceptable."""
    request = ctx.request_context.request
    token = _bearer_from(request.headers.get("authorization", "")) if request else ""
    return await asyncio.to_thread(validate_token, token)


@mcp.tool()
async def my_profile(ctx: Context) -> dict:
    """Get the signed-in user's own profile (name, email, job title, department)
    from Microsoft Graph. Takes no arguments: it always returns the caller's own data."""
    user = await _caller(ctx)

    graph_token = await asyncio.to_thread(obo.graph_token_for, user.access_token)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(config.GRAPH_ME_URL, headers={"Authorization": f"Bearer {graph_token}"})

    log.info("tool=my_profile oid=%s roles=%s graph_status=%s", user.oid, user.roles, resp.status_code)
    resp.raise_for_status()
    profile = resp.json()
    profile.pop("@odata.context", None)
    return profile


@mcp.tool()
async def create_it_ticket(title: str, description: str, ctx: Context) -> dict:
    """Create an IT support ticket. Only users with the IT role may do this."""
    user = await _caller(ctx)

    # Tool-level authorization: checked here, from the validated token.
    if "IT" not in user.roles:
        log.warning("tool=create_it_ticket oid=%s roles=%s decision=403", user.oid, user.roles)
        raise PermissionError("403 Forbidden: only users with the IT role can create IT tickets.")

    with _lock:
        ticket = {
            "id": f"IT-{next(_ticket_ids)}",
            "title": title[:200],
            "description": description[:2000],
            "created_by": user.oid,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "open",
        }
        _tickets.append(ticket)

    log.info("tool=create_it_ticket oid=%s roles=%s decision=allow ticket=%s", user.oid, user.roles, ticket["id"])
    return ticket


class RequireBearer:
    """ASGI wrapper: reject any MCP HTTP request without a valid token before
    the MCP server sees it (so even listing tools needs a valid token)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers") or [])
            token = _bearer_from(headers.get(b"authorization", b"").decode())
            try:
                await asyncio.to_thread(validate_token, token)
            except AuthError as e:
                log.warning("mcp rejected (%s): %s", e.status_code, e.reason)
                detail = "Invalid or missing token" if e.status_code == 401 else "Access denied"
                await JSONResponse({"detail": detail}, status_code=e.status_code)(scope, receive, send)
                return
        await self.app(scope, receive, send)


# Endpoint inside this app: /tools (mount) + /mcp (FastMCP default path)
mcp_http_app = RequireBearer(mcp.streamable_http_app())