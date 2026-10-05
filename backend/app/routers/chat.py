import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user

log = logging.getLogger("askhr.chat")
router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: CurrentUser = Depends(get_current_user)):
    # Log who asked, not what they asked: messages may contain personal data.
    log.info("chat oid=%s name=%s roles=%s message_len=%d",
             user.oid, user.name, user.roles, len(req.message))

    reply = (
        f"(Phase 2 placeholder) Hi {user.name}, your roles are {user.roles}. "
        "The agent arrives in Phase 3."
    )
    return ChatResponse(reply=reply)