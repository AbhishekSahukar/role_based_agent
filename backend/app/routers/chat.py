import logging

from fastapi import APIRouter, Depends, HTTPException
from langgraph.errors import GraphRecursionError
from openai import APIStatusError, RateLimitError
from pydantic import BaseModel, Field

from app.agent import run_agent
from app.auth import CurrentUser, get_current_user

log = logging.getLogger("askhr.chat")
router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: CurrentUser = Depends(get_current_user)):
    # Log who asked, not what they asked: messages may contain personal data.
    log.info("chat oid=%s name=%s roles=%s message_len=%d",
             user.oid, user.name, user.roles, len(req.message))
    try:
        reply = await run_agent(user, req.message)
    except RateLimitError:
        log.warning("llm rate limited oid=%s", user.oid)
        raise HTTPException(429, "The assistant is busy right now. Please try again in a minute.")
    except APIStatusError as e:
        if e.status_code == 402:
            log.error("llm payment required (402): check OpenRouter credit balance")
            raise HTTPException(503, "The assistant is temporarily unavailable.")
        log.error("llm error status=%s message=%s", e.status_code, e.message)
        raise HTTPException(502, "The assistant could not answer. Please try again.")
    except GraphRecursionError:
        log.warning("agent hit recursion limit oid=%s", user.oid)
        raise HTTPException(500, "The assistant got stuck on that question. Please rephrase it.")
    except Exception:
        # e.g. MCP server unreachable. Log the details, return a generic message.
        log.exception("agent failed oid=%s", user.oid)
        raise HTTPException(502, "The assistant could not answer. Please try again.")

    log.info("chat done oid=%s reply_len=%d", user.oid, len(reply))
    return ChatResponse(reply=reply)