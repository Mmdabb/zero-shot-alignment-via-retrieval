"""Gemini provider."""

import logging
import os

from alignment.prompts import build_aligned_response_prompt, build_base_response_prompt

from .base import BaseLLMProvider, ProviderResult

try:
    from google import genai
except ImportError:
    genai = None


logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Hosted fallback provider backed by Gemini."""

    name = "gemini"

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = None

        if self.api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as exc:
                logger.warning("Gemini client initialization failed: %s", exc)

    def is_available(self) -> bool:
        return self.client is not None

    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{system_prompt}\n\n{user_prompt}",
        )
        return (getattr(response, "text", "") or "").strip()

    def generate_base_response(self, user_query: str) -> ProviderResult:
        try:
            system_prompt, user_prompt = build_base_response_prompt(user_query)
            text = self._generate(system_prompt, user_prompt)
            if not text:
                raise RuntimeError("Gemini returned an empty response.")
            return ProviderResult(text, self.name, self.model, True)
        except Exception as exc:
            logger.exception("Gemini base generation failed")
            return ProviderResult("", self.name, self.model, False, str(exc))

    def generate_aligned_response(
        self,
        user_query: str,
        base_response: str,
        style_name: str,
        style_description: str,
        style_schema: dict,
    ) -> ProviderResult:
        try:
            system_prompt, user_prompt = build_aligned_response_prompt(
                user_query, base_response, style_name, style_description, style_schema
            )
            text = self._generate(system_prompt, user_prompt)
            if not text:
                raise RuntimeError("Gemini returned an empty response.")
            return ProviderResult(text, self.name, self.model, True)
        except Exception as exc:
            logger.exception("Gemini alignment generation failed")
            return ProviderResult("", self.name, self.model, False, str(exc))
