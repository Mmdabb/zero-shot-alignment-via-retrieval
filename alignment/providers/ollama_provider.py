"""Local Ollama provider."""

import logging
import os

import requests

from alignment.prompts import build_aligned_response_prompt, build_base_response_prompt

from .base import BaseLLMProvider, ProviderResult


logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Local fallback provider backed by Ollama."""

    name = "ollama"

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=0.4)
            return response.ok
        except Exception:
            return False

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["message"]["content"].strip()

    def generate_base_response(self, user_query: str) -> ProviderResult:
        try:
            system_prompt, user_prompt = build_base_response_prompt(user_query)
            return ProviderResult(self._chat(system_prompt, user_prompt), self.name, self.model, True)
        except Exception as exc:
            logger.exception("Ollama base generation failed")
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
            logger.exception("Ollama alignment generation failed")
            return ProviderResult("", self.name, self.model, False, str(exc))
