"""Multi-provider LLM client with transparent fallback attempts."""

import logging
import os
from pathlib import Path
from typing import Callable

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from .providers.base import BaseLLMProvider, ProviderResult
from .providers.gemini_provider import GeminiProvider
from .providers.github_provider import GitHubModelsProvider
from .providers.groq_provider import GroqProvider
from .providers.ollama_provider import OllamaProvider
from .providers.schema_provider import SchemaProvider


logger = logging.getLogger(__name__)


class LLMClient:
    """Manage base generation and alignment across configured providers."""

    DEFAULT_PROVIDER_ORDER = "github,gemini,groq,ollama,schema"

    def __init__(self):
        self._load_environment()
        self.provider_order = self._provider_order()
        self.providers = self._load_providers()
        logger.info("Loaded environment variables")
        logger.info("Active provider order: %s", ",".join(self.provider_order))

    def _load_environment(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        env_path = project_root / ".env"
        if load_dotenv is not None and env_path.exists():
            load_dotenv(dotenv_path=env_path)

        self.use_llm = os.getenv("USE_LLM", "true").strip().lower() in {"1", "true", "yes"}

    def _provider_order(self) -> list[str]:
        configured = os.getenv("LLM_PROVIDER_ORDER", self.DEFAULT_PROVIDER_ORDER)
        order = [item.strip().lower() for item in configured.split(",") if item.strip()]
        if "schema" not in order:
            order.append("schema")
        if not self.use_llm:
            return ["schema"]
        return order

    def _load_providers(self) -> dict[str, BaseLLMProvider]:
        providers: dict[str, BaseLLMProvider] = {
            "github": GitHubModelsProvider(),
            "gemini": GeminiProvider(),
            "groq": GroqProvider(),
            "ollama": OllamaProvider(),
            "schema": SchemaProvider(),
        }
        return {name: providers[name] for name in self.provider_order if name in providers}

    def is_available(self) -> bool:
        """Return True when at least one non-schema provider is available."""
        return any(
            name != "schema" and provider.is_available()
            for name, provider in self.providers.items()
        )

    def generation_mode(self) -> str:
        """Return a compact generation mode for legacy callers."""
        return "llm" if self.is_available() else "schema_fallback"

    def _unavailable_model(self, provider: BaseLLMProvider) -> str:
        return getattr(provider, "model", "unconfigured")

    def _run_provider_chain(
        self,
        task: str,
        generate: Callable[[BaseLLMProvider], ProviderResult],
    ) -> dict:
        attempts = []

        for name, provider in self.providers.items():
            model = self._unavailable_model(provider)
            logger.info("Trying provider=%s task=%s model=%s", name, task, model)

            if not provider.is_available():
                error = "provider unavailable or missing credentials"
                logger.warning("Provider failure provider=%s task=%s error=%s", name, task, error)
                attempts.append({
                    "task": task,
                    "provider": name,
                    "model": model,
                    "success": False,
                    "error": error,
                })
                continue

            result = generate(provider)
            attempts.append({
                "task": task,
                "provider": result.provider,
                "model": result.model,
                "success": result.success,
                "error": result.error,
            })

            if result.success and result.text:
                logger.info("Provider success provider=%s task=%s model=%s", result.provider, task, result.model)
                return {
                    "text": result.text,
                    "provider": result.provider,
                    "model": result.model,
                    "success": True,
                    "error": None,
                    "attempts": attempts,
                }

            logger.warning(
                "Provider failure provider=%s task=%s error=%s",
                result.provider,
                task,
                result.error,
            )

        schema = SchemaProvider()
        result = generate(schema)
        attempts.append({
            "task": task,
            "provider": result.provider,
            "model": result.model,
            "success": result.success,
            "error": result.error,
        })
        return {
            "text": result.text,
            "provider": result.provider,
            "model": result.model,
            "success": True,
            "error": result.error,
            "attempts": attempts,
        }

    def generate_base_response(self, user_query: str) -> dict:
        """Generate a neutral response using the provider chain."""
        return self._run_provider_chain(
            "base_generation",
            lambda provider: provider.generate_base_response(user_query),
        )

    def generate_aligned_response(
        self,
        user_query: str,
        base_response: str,
        style_name: str,
        style_description: str,
        style_schema: dict,
    ) -> dict:
        """Rewrite a response using the provider chain."""
        return self._run_provider_chain(
            "alignment_generation",
            lambda provider: provider.generate_aligned_response(
                user_query=user_query,
                base_response=base_response,
                style_name=style_name,
                style_description=style_description,
                style_schema=style_schema,
            ),
        )
