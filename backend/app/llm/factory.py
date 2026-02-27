from .anthropic_provider import AnthropicProvider
from .base import LLMProvider
from .google_provider import GoogleProvider
from .openai_provider import OpenAIProvider

PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "google_ai": GoogleProvider,
}


def get_provider(
    name: str, api_key: str, model: str | None = None
) -> LLMProvider:
    """Instantiate and return an LLM provider by name.

    Args:
        name: Provider identifier (anthropic, openai, google_ai).
        api_key: API key for the chosen provider.
        model: Optional model override; defaults to the provider\'s default.

    Returns:
        An initialized LLMProvider instance.

    Raises:
        ValueError: If the provider name is not recognized.
    """
    cls = PROVIDERS.get(name)
    if not cls:
        raise ValueError(
            f"Unknown LLM provider: {name}. Available: {list(PROVIDERS.keys())}"
        )
    return cls(api_key=api_key, model=model)
