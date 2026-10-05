import logging

from app import config

log = logging.getLogger("askhr.tracing")


def get_callbacks() -> list:
    """Langfuse callback handler, or nothing if tracing isn't configured.
    Langfuse reads LANGFUSE_PUBLIC_KEY / SECRET_KEY / HOST from the environment."""
    if not config.LANGFUSE_ENABLED:
        return []
    try:
        from langfuse.langchain import CallbackHandler
        return [CallbackHandler()]
    except Exception as e:  # tracing must never break the chat
        log.warning("Langfuse disabled: %s", e)
        return []