"""LLM provider — OpenRouter via OpenAI-compatible API."""

from langchain_openai import ChatOpenAI

from config import get_settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def has_llm() -> bool:
    """Return True when an OpenRouter API key is configured."""
    return bool(get_settings().openrouter_api_key.strip())


def _normalize_model_id(model: str) -> str:
    """Strip optional 'openrouter:' prefix from model id."""
    if model.startswith("openrouter:"):
        return model.removeprefix("openrouter:")
    return model


def get_chat_model(*, streaming: bool = False, temperature: float = 0.1) -> ChatOpenAI:
    """Return a ChatOpenAI client pointed at OpenRouter."""
    settings = get_settings()
    if not has_llm():
        raise ValueError("OPENROUTER_API_KEY is not configured")

    headers: dict[str, str] = {}
    if settings.openrouter_site_url:
        headers["HTTP-Referer"] = settings.openrouter_site_url
    if settings.openrouter_app_name:
        headers["X-Title"] = settings.openrouter_app_name

    return ChatOpenAI(
        model=_normalize_model_id(settings.openrouter_model),
        openai_api_key=settings.openrouter_api_key,
        openai_api_base=settings.openrouter_base_url or OPENROUTER_BASE_URL,
        temperature=temperature,
        streaming=streaming,
        default_headers=headers or None,
       
    )
