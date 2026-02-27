import logging
from typing import AsyncIterator

import anthropic

from .base import LLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """LLM provider implementation for Anthropic Claude models."""

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-20250514"

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key=api_key, model=model)
        self._client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
            )
            if response.content and len(response.content) > 0:
                return response.content[0].text
            return ""
        except anthropic.AuthenticationError as exc:
            logger.error("Anthropic authentication failed: %s", exc)
            raise ValueError("Invalid Anthropic API key.") from exc
        except anthropic.RateLimitError as exc:
            logger.warning("Anthropic rate limit hit: %s", exc)
            raise RuntimeError(
                "Anthropic rate limit exceeded. Please retry later."
            ) from exc
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s", exc)
            raise RuntimeError(f"Anthropic API error: {exc}") from exc

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        try:
            async with self._client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except anthropic.AuthenticationError as exc:
            logger.error("Anthropic authentication failed: %s", exc)
            raise ValueError("Invalid Anthropic API key.") from exc
        except anthropic.RateLimitError as exc:
            logger.warning("Anthropic rate limit hit: %s", exc)
            raise RuntimeError(
                "Anthropic rate limit exceeded. Please retry later."
            ) from exc
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s", exc)
            raise RuntimeError(f"Anthropic API error: {exc}") from exc

    async def list_models(self) -> list[str]:
        try:
            models_page = await self._client.models.list(limit=100)
            return sorted([model.id for model in models_page.data])
        except anthropic.APIError as exc:
            logger.error("Failed to list Anthropic models: %s", exc)
            raise RuntimeError(
                f"Failed to list Anthropic models: {exc}"
            ) from exc
