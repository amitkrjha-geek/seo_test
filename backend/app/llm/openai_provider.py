import logging
from typing import AsyncIterator

import openai
from openai import AsyncOpenAI

from .base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """LLM provider implementation for OpenAI models."""

    @property
    def default_model(self) -> str:
        return "gpt-4o"

    @property
    def provider_name(self) -> str:
        return "openai"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key=api_key, model=model)
        self._client = AsyncOpenAI(api_key=self.api_key)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            choice = response.choices[0] if response.choices else None
            if choice and choice.message and choice.message.content:
                return choice.message.content
            return ""
        except openai.AuthenticationError as exc:
            logger.error("OpenAI authentication failed: %s", exc)
            raise ValueError("Invalid OpenAI API key.") from exc
        except openai.RateLimitError as exc:
            logger.warning("OpenAI rate limit hit: %s", exc)
            raise RuntimeError(
                "OpenAI rate limit exceeded. Please retry later."
            ) from exc
        except openai.APIError as exc:
            logger.error("OpenAI API error: %s", exc)
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            async for chunk in response:
                choice = chunk.choices[0] if chunk.choices else None
                if choice and choice.delta and choice.delta.content:
                    yield choice.delta.content
        except openai.AuthenticationError as exc:
            logger.error("OpenAI authentication failed: %s", exc)
            raise ValueError("Invalid OpenAI API key.") from exc
        except openai.RateLimitError as exc:
            logger.warning("OpenAI rate limit hit: %s", exc)
            raise RuntimeError(
                "OpenAI rate limit exceeded. Please retry later."
            ) from exc
        except openai.APIError as exc:
            logger.error("OpenAI API error: %s", exc)
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

    async def list_models(self) -> list[str]:
        try:
            models_page = await self._client.models.list()
            return sorted([model.id async for model in models_page])
        except openai.APIError as exc:
            logger.error("Failed to list OpenAI models: %s", exc)
            raise RuntimeError(
                f"Failed to list OpenAI models: {exc}"
            ) from exc
