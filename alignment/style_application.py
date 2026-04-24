"""Style Application Module - Builds style prompts and delegates rewrites."""

from typing import Optional

from .llm_client import LLMClient
from .style_schema import get_style_schema
from .style_library import StyleLibrary


class StyleApplicator:
    """Applies style to responses through the multi-provider LLM client."""

    def __init__(self, style_library: StyleLibrary, llm_client: Optional[LLMClient] = None):
        self.style_library = style_library
        self.llm_client = llm_client or LLMClient()

    def create_style_prompt(self, style_name: str) -> str:
        """Create a prompt prefix for the given style."""
        style = self.style_library.get_style(style_name)
        examples = " ".join(style.examples)
        return (
            f"You MUST respond in a {style_name} tone. "
            f"Description: {style.description}. "
            f"Examples: {examples}"
        )

    def augment_prompt(self, original_prompt: str, style_name: str) -> str:
        """Augment a prompt with style instructions."""
        style_prompt = self.create_style_prompt(style_name)
        return f"{style_prompt}\n\nUser request: {original_prompt}"

    def apply_style_to_response(self, response: str, style_name: str) -> str:
        """Apply style through the schema provider path for legacy callers."""
        result = self.generate_aligned_response("", response, style_name)
        if isinstance(result, dict):
            return result["text"]
        return result

    def generate_aligned_response(self, user_query: str, base_response: str, style_name: str) -> dict:
        """Generate or rewrite the final aligned response."""
        style = self.style_library.get_style(style_name)
        return self.llm_client.generate_aligned_response(
            user_query=user_query,
            base_response=base_response,
            style_name=style_name,
            style_description=style.description,
            style_schema=get_style_schema(style_name),
        )

    def get_style_description(self, style_name: str) -> str:
        """Get human-readable description of a style."""
        return self.style_library.get_style(style_name).description
