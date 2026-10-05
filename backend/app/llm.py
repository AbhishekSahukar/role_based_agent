from langchain_openai import ChatOpenAI

from app import config


def build_llm() -> ChatOpenAI:
    # OpenRouter speaks the OpenAI API, so the OpenAI client works unchanged.
    # max_retries: the OpenAI client retries 429s and 5xx with exponential
    # backoff and honours Retry-After. 402 (no credit) is NOT retried.
    return ChatOpenAI(
        model=config.LLM_MODEL,
        base_url=config.OPENROUTER_BASE_URL,
        api_key=config.OPENROUTER_API_KEY,
        max_retries=config.LLM_MAX_RETRIES,
        timeout=config.LLM_TIMEOUT_SECONDS,
        temperature=0,
    )