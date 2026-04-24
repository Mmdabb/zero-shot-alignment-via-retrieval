"""GitHub Models provider using OpenAI-compatible chat completions."""

import logging
import os

from alignment.prompts import build_aligned_response_prompt, build_base_response_prompt

from .base import BaseLLMProvider, ProviderResult

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


logger = logging.getLogger(__name__)


class GitHubModelsProvider(BaseLLMProvider):
    """Hosted demo provider backed by GitHub Models."""

    name = "github"

    def __init__(self):
        self.api_key = os.getenv("GITHUB_TOKEN")
        self.model = os.getenv("GITHUB_MODEL", "openai/gpt-4o-mini")
        self.base_url = os.getenv(
            "GITHUB_MODELS_BASE_URL",
            "https://models.github.ai/inference",
        )
        self.client = None

        if self.api_key and OpenAI is not None:
            try:
                self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            except Exception as exc:
                logger.warning("GitHub Models client initialization failed: %s", exc)

    def is_available(self) -> bool:
        return self.client is not None

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    def generate_base_response(self, user_query: str) -> ProviderResult:
        try:
            system_prompt, user_prompt = build_base_response_prompt(user_query)
            return ProviderResult(self._chat(system_prompt, user_prompt), self.name, self.model, True)
        except Exception as exc:
            logger.exception("GitHub Models base generation failed")
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
            return ProviderResult(self._chat(system_prompt, user_prompt), self.name, self.model, True)
        except Exception as exc:
            logger.exception("GitHub Models alignment generation failed")
            return ProviderResult("", self.name, self.model, False, str(exc))
