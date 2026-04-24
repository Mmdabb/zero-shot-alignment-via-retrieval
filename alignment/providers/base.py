"""Shared provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderResult:
    text: str
    provider: str
    model: str
    success: bool
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """Base class for all LLM providers."""

    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the provider can be attempted."""

    @abstractmethod
    def generate_base_response(self, user_query: str) -> ProviderResult:
        """Generate a neutral base response."""

    @abstractmethod
    def generate_aligned_response(
        self,
        user_query: str,
        base_response: str,
        style_name: str,
        style_description: str,
        style_schema: dict,
    ) -> ProviderResult:
        """Generate a style-aligned response."""
