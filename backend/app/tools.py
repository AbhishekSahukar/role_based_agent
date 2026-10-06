import logging
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app import retrieval

log = logging.getLogger("askhr.tools")

# InjectedState: ToolNode fills this parameter from the graph state.
# It is removed from the schema the LLM sees, so the model can neither
# read nor set oid/roles. Permissions flow code -> code, never via the prompt.


@tool
def get_my_access(state: Annotated[dict, InjectedState]) -> str:
    """Report the signed-in user's verified AskHR roles.
    Use this when the user asks about their own access, role or permissions,
    or claims to have a role."""
    roles = state["roles"]
    log.info("tool=get_my_access oid=%s roles=%s", state["oid"], roles)
    return (
        f"The signed-in user's verified roles are: {', '.join(roles)}. "
        "These come from their Entra ID sign-in and cannot be changed in chat."
    )


@tool
def search_policies(query: str, state: Annotated[dict, InjectedState]) -> str:
    """Search internal HR and IT policy documents (leave, salary bands,
    equipment, passwords, travel, security procedures, etc.).
    Use this for any policy question. Pass a short keyword query."""
    oid, roles = state["oid"], state["roles"]
    log.info("tool=search_policies oid=%s roles=%s query_len=%d", oid, roles, len(query))

    docs = retrieval.search_policies(query=query, roles=roles, oid=oid)
    if not docs:
        return "No policy documents available to this user match the query."

    parts = [f"[{d['title']}] (id: {d['id']})\n{d['content']}" for d in docs]
    return (
        "Policy documents available to this user. Answer only from these; if none "
        "of them actually answers the question, say you can't find that information.\n\n"
        + "\n\n---\n\n".join(parts)
    )


TOOLS = [get_my_access, search_policies]