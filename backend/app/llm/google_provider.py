import logging
from typing import AsyncIterator

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from .base import LLMProvider

logger = logging.getLogger(__name__)


class GoogleProvider(LLMProvider):
    """LLM provider implementation for Google Gemini models."""

    @property
    def default_model(self) -> str:
        return "gemini-2.0-flash"

    @property
    def provider_name(self) -> str:
        return "google_ai"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key=api_key, model=model)
        self._client = genai.Client(api_key=self.api_key)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            if response.text:
                return response.text
            return ""
        except genai_errors.ClientError as exc:
            logger.error("Google AI client error: %s", exc)
            raise ValueError(f"Google AI client error: {exc}") from exc
        except genai_errors.ServerError as exc:
            logger.error("Google AI server error: %s", exc)
            raise RuntimeError(f"Google AI server error: {exc}") from exc
        except Exception as exc:
            logger.error("Google AI unexpected error: %s", exc)
            raise RuntimeError(f"Google AI error: {exc}") from exc

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        try:
            async for chunk in self._client.aio.models.generate_content_stream(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            ):
                if chunk.text:
                    yield chunk.text
        except genai_errors.ClientError as exc:
            logger.error("Google AI client error: %s", exc)
            raise ValueError(f"Google AI client error: {exc}") from exc
        except genai_errors.ServerError as exc:
            logger.error("Google AI server error: %s", exc)
            raise RuntimeError(f"Google AI server error: {exc}") from exc
        except Exception as exc:
            logger.error("Google AI unexpected error: %s", exc)
            raise RuntimeError(f"Google AI error: {exc}") from exc

    async def list_models(self) -> list[str]:
        try:
            models = []
            async for model in self._client.aio.models.list():
                models.append(model.name)
            return sorted(models)
        except Exception as exc:
            logger.error("Failed to list Google AI models: %s", exc)
            raise RuntimeError(
                f"Failed to list Google AI models: {exc}"
            ) from exc
