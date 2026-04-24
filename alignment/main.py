"""Main Entry Point - Demonstrates the zero-shot alignment system."""

import logging
from typing import Optional

from .embeddings import EmbeddingModule
from .llm_client import LLMClient
from .logging_config import get_log_path, setup_logging
from .retrieval import RetrievalModule
from .style_application import StyleApplicator
from .style_library import StyleLibrary

logger = logging.getLogger(__name__)


class ZeroShotAlignmentSystem:
    """Complete zero-shot alignment system combining all modules."""

    def __init__(self):
        """Initialize all system components."""
        setup_logging()
        self.style_library = StyleLibrary()
        self.embedding_module = EmbeddingModule()
        self.retrieval_module = RetrievalModule(self.embedding_module)
        self.llm_client = LLMClient()
        self.style_applicator = StyleApplicator(self.style_library, self.llm_client)
        self.retrieval_module.index_styles(self.style_library.styles)

    def align_response(self, prompt: str, response: Optional[str] = None) -> dict:
        """
        Retrieve a style, generate or accept a base response, and align the final response.

        Args:
            prompt: User query.
            response: Optional base response override.

        Returns:
            JSON-friendly dictionary with alignment results.
        """
        best_style = self.retrieval_module.retrieve_single(prompt, self.style_library.styles)
        top_styles = [
            [style_name, float(score)]
            for style_name, score in self.retrieval_module.retrieve_top_k(prompt, self.style_library.styles, k=4)
        ]
        style = self.style_library.get_style(best_style)

        logger.info("User query received length=%s", len(prompt))
        logger.info("Retrieved style=%s", best_style)
        logger.info("Top-k style scores=%s", top_styles)

        if response and response.strip():
            base_response = response.strip()
            base_response_source = "user_override"
            base_provider = "user"
            base_model = "manual-override"
            base_attempts = []
            logger.info("Base response was user override")
        else:
            base_result = self.llm_client.generate_base_response(prompt)
            base_response = base_result["text"]
            base_response_source = "auto_generated"
            base_provider = base_result["provider"]
            base_model = base_result["model"]
            base_attempts = base_result["attempts"]
            logger.info("Base response was auto-generated")
            logger.info("Final selected base provider=%s model=%s", base_provider, base_model)

        alignment_result = self.style_applicator.generate_aligned_response(prompt, base_response, best_style)
        styled_response = alignment_result["text"]
        logger.info(
            "Final selected alignment provider=%s model=%s",
            alignment_result["provider"],
            alignment_result["model"],
        )

        return {
            "original_prompt": prompt,
            "base_response": base_response,
            "best_style": best_style,
            "top_styles": top_styles,
            "style_prompt_augmentation": self.style_applicator.create_style_prompt(best_style),
            "styled_response": styled_response,
            "generation_mode": self.llm_client.generation_mode(),
            "base_response_source": base_response_source,
            "base_provider": base_provider,
            "base_model": base_model,
            "alignment_provider": alignment_result["provider"],
            "alignment_model": alignment_result["model"],
            "retrieval_model": self.embedding_module.active_model_name,
            "provider_attempts": base_attempts + alignment_result["attempts"],
            "style_schema": style.name,
            "log_file": get_log_path(),
        }

    def demo(self) -> None:
        """Run a demonstration of the alignment system."""
        print("\n" + "=" * 70)
        print("ZERO-SHOT ALIGNMENT VIA RETRIEVAL - SYSTEM DEMO")
        print("=" * 70)

        test_cases = [
            "Write a professional email to a professor",
            "Explain the algorithm and implementation details",
            "Can you explain this like a friend?",
            "Tell me casually what this project does",
        ]

        for prompt in test_cases:
            result = self.align_response(prompt)

            print("\n--- Test Case ---")
            print(f"Prompt: {result['original_prompt']}")
            print(f"Retrieval Model: {result['retrieval_model']}")
            print(f"Generation Mode: {result['generation_mode']}")
            print(f"Base Response Source: {result['base_response_source']}")
            print(f"Base Provider: {result['base_provider']} / {result['base_model']}")
            print(f"Alignment Provider: {result['alignment_provider']} / {result['alignment_model']}")
            print(f"Before Alignment: {result['base_response']}")
            print(f"Best Matched Style: {result['best_style']}")
            print("Top-4 Styles (with scores):")
            for style_name, score in result["top_styles"]:
                print(f"  - {style_name}: {score:.4f}")
            print(f"After Alignment: {result['styled_response']}")
            print(f"Log File: {result['log_file']}")


def main() -> None:
    """Main entry point."""
    system = ZeroShotAlignmentSystem()
    system.demo()


if __name__ == "__main__":
    main()
