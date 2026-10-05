import logging
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

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
    equipment, passwords, travel, etc.). Use this for any policy question."""
    roles = state["roles"]
    # Phase 4: build the allowed_roles filter from `roles` here.
    log.info("tool=search_policies oid=%s roles=%s query_len=%d filter=not-yet-built",
             state["oid"], roles, len(query))
    return (
        "Policy search is not connected yet. Tell the user you cannot look up "
        "policy documents at the moment."
    )


TOOLS = [get_my_access, search_policies]