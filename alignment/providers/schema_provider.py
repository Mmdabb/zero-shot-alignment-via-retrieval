"""Always-available schema fallback provider."""

import logging

from alignment.fallback_generator import generate_fallback_base_response, schema_rewrite

from .base import BaseLLMProvider, ProviderResult


logger = logging.getLogger(__name__)


class SchemaProvider(BaseLLMProvider):
    """No-API fallback provider using deterministic schema rewrites."""

    name = "schema"
    model = "schema-fallback-v1"

    def is_available(self) -> bool:
        return True

    def generate_base_response(self, user_query: str) -> ProviderResult:
        try:
            text = generate_fallback_base_response(user_query)
            return ProviderResult(text, self.name, self.model, True)
        except Exception as exc:
            logger.exception("Schema base generation failed")
            return ProviderResult(
                "The user's request can be answered by explaining the key idea clearly.",
                self.name,
                self.model,
                True,
                str(exc),
            )

    def generate_aligned_response(
        self,
        user_query: str,
        base_response: str,
        style_name: str,
        style_description: str,
        style_schema: dict,
    ) -> ProviderResult:
        try:
            text = schema_rewrite(base_response, style_name, style_schema)
            return ProviderResult(text, self.name, self.model, True)
        except Exception as exc:
            logger.exception("Schema alignment generation failed")
            return ProviderResult(base_response, self.name, self.model, True, str(exc))
