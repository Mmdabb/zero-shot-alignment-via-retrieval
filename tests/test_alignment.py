"""Comprehensive Tests for Zero-Shot Alignment System."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alignment.style_library import StyleLibrary, Style
from alignment.embeddings import EmbeddingModule
from alignment.retrieval import RetrievalModule
from alignment.style_application import StyleApplicator
from alignment.main import ZeroShotAlignmentSystem
from pathlib import Path


class TestStyleLibrary:
    """Test the style library module."""

    def test_load_default_styles(self):
        """Test that default styles are loaded."""
        lib = StyleLibrary()
        assert len(lib.list_styles()) == 4
        assert "formal" in lib.list_styles()
        assert "casual" in lib.list_styles()
        assert "technical" in lib.list_styles()
        assert "friendly" in lib.list_styles()
        print("[PASS] test_load_default_styles")

    def test_get_style(self):
        """Test retrieving a style."""
        lib = StyleLibrary()
        style = lib.get_style("formal")
        assert isinstance(style, Style)
        assert style.name == "formal"
        assert len(style.examples) > 0
        print("[PASS] test_get_style")

    def test_invalid_style(self):
        """Test that invalid style raises error."""
        lib = StyleLibrary()
        try:
            lib.get_style("nonexistent")
            assert False, "Should raise ValueError"
        except ValueError:
            pass
        print("[PASS] test_invalid_style")

    def test_get_style_descriptions(self):
        """Test getting all style descriptions."""
        lib = StyleLibrary()
        descs = lib.get_style_descriptions()
        assert len(descs) == 4
        assert "formal" in descs
        print("[PASS] test_get_style_descriptions")


class TestEmbeddingModule:
    """Test the embedding module."""

    def test_embed_text(self):
        """Test embedding generation."""
        emb = EmbeddingModule(embedding_dim=128)
        embedding = emb.embed_text("hello world")
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
        print("[PASS] test_embed_text")

    def test_deterministic_embedding(self):
        """Test that same text produces same embedding."""
        emb = EmbeddingModule()
        emb1 = emb.embed_text("test")
        emb2 = emb.embed_text("test")
        assert emb1 == emb2
        print("[PASS] test_deterministic_embedding")

    def test_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        emb = EmbeddingModule()
        emb1 = emb.embed_text("hello")
        emb2 = emb.embed_text("goodbye")
        assert emb1 != emb2
        print("[PASS] test_different_embeddings")

    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        emb = EmbeddingModule()
        
        # Same vectors should have similarity 1.0
        vec = [1.0, 0.0, 0.0]
        sim = emb.cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 0.001
        
        # Orthogonal vectors should have similarity 0.0
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        sim = emb.cosine_similarity(vec1, vec2)
        assert abs(sim - 0.0) < 0.001
        
        print("[PASS] test_cosine_similarity")

    def test_batch_embed(self):
        """Test batch embedding."""
        emb = EmbeddingModule()
        texts = ["hello", "world", "test"]
        embeddings = emb.embed_batch(texts)
        assert len(embeddings) == 3
        assert all(len(e) == len(embeddings[0]) for e in embeddings)
        print("[PASS] test_batch_embed")

    def test_compute_similarity(self):
        """Test text similarity computation."""
        emb = EmbeddingModule()
        sim = emb.compute_similarity("hello", "hello")
        assert abs(sim - 1.0) < 0.001
        print("[PASS] test_compute_similarity")


class TestRetrievalModule:
    """Test the retrieval module."""

    def test_retrieve_top_k(self):
        """Test top-k retrieval."""
        lib = StyleLibrary()
        emb = EmbeddingModule()
        retrieval = RetrievalModule(emb)
        
        results = retrieval.retrieve_top_k("professional business", lib.styles, k=2)
        assert len(results) == 2
        assert all(isinstance(name, str) and isinstance(score, float) for name, score in results)
        print("[PASS] test_retrieve_top_k")

    def test_retrieve_single(self):
        """Test single style retrieval."""
        lib = StyleLibrary()
        emb = EmbeddingModule()
        retrieval = RetrievalModule(emb)
        
        best_style = retrieval.retrieve_single("technical specs", lib.styles)
        assert best_style in lib.list_styles()
        print("[PASS] test_retrieve_single")

    def test_indexing(self):
        """Test style indexing."""
        lib = StyleLibrary()
        emb = EmbeddingModule()
        retrieval = RetrievalModule(emb)
        
        assert len(retrieval.style_embeddings) == 0
        retrieval.index_styles(lib.styles)
        assert len(retrieval.style_embeddings) == 4
        print("[PASS] test_indexing")

    def test_semantic_retrieval_examples(self):
        """Test that style-intent examples retrieve the expected style."""
        lib = StyleLibrary()
        emb = EmbeddingModule()
        retrieval = RetrievalModule(emb)

        examples = [
            ("Write a professional email to a professor", "formal"),
            ("Explain the algorithm and implementation details", "technical"),
            ("Can you explain this like a friend?", "friendly"),
            ("Tell me casually what this project does", "casual"),
        ]

        correct = 0
        for prompt, expected_style in examples:
            if retrieval.retrieve_single(prompt, lib.styles) == expected_style:
                correct += 1

        assert correct >= 3
        print("[PASS] test_semantic_retrieval_examples")


class TestStyleApplicator:
    """Test the style applicator module."""

    def test_create_style_prompt(self):
        """Test style prompt creation."""
        lib = StyleLibrary()
        applicator = StyleApplicator(lib)
        
        prompt = applicator.create_style_prompt("formal")
        assert "formal" in prompt
        assert "description" in prompt.lower()
        print("[PASS] test_create_style_prompt")

    def test_augment_prompt(self):
        """Test prompt augmentation."""
        lib = StyleLibrary()
        applicator = StyleApplicator(lib)
        
        original = "What is AI?"
        augmented = applicator.augment_prompt(original, "technical")
        assert "technical" in augmented
        assert original in augmented
        print("[PASS] test_augment_prompt")

    def test_apply_style_to_response(self):
        """Test response styling."""
        lib = StyleLibrary()
        applicator = StyleApplicator(lib)
        
        response = "Hi, okay, yeah"
        styled_formal = applicator.apply_style_to_response(response, "formal")
        styled_casual = applicator.apply_style_to_response(response, "casual")
        
        assert styled_formal != response or styled_casual != response
        print("[PASS] test_apply_style_to_response")

    def test_get_style_description(self):
        """Test getting style description."""
        lib = StyleLibrary()
        applicator = StyleApplicator(lib)
        
        desc = applicator.get_style_description("friendly")
        assert len(desc) > 0
        assert "Warm" in desc or "warm" in desc
        print("[PASS] test_get_style_description")


class TestZeroShotAlignmentSystem:
    """Test the complete system."""

    def test_system_initialization(self):
        """Test system initialization."""
        system = ZeroShotAlignmentSystem()
        assert system.style_library is not None
        assert system.embedding_module is not None
        assert system.retrieval_module is not None
        assert system.style_applicator is not None
        print("[PASS] test_system_initialization")

    def test_align_response(self):
        """Test end-to-end alignment."""
        system = ZeroShotAlignmentSystem()
        
        prompt = "Please explain this formally"
        response = "It is what it is"
        
        result = system.align_response(prompt, response)
        
        assert "best_style" in result
        assert "styled_response" in result
        assert "top_styles" in result
        assert "generation_mode" in result
        assert "base_response_source" in result
        assert "base_provider" in result
        assert "alignment_provider" in result
        assert "provider_attempts" in result
        assert "log_file" in result
        assert "retrieval_model" in result
        assert len(result["top_styles"]) == 4
        assert result["best_style"] in system.style_library.list_styles()
        
        print("[PASS] test_align_response")

    def test_auto_base_response_generation(self):
        """Test that the system can generate a base response automatically."""
        system = ZeroShotAlignmentSystem()

        prompt = "Explain the technical architecture of the system"
        result = system.align_response(prompt)

        assert "base_response" in result
        assert len(result["base_response"]) > 0
        assert result["base_response"] != result["original_prompt"]
        assert result["base_response_source"] == "auto_generated"
        assert result["best_style"] in system.style_library.list_styles()
        print("[PASS] test_auto_base_response_generation")

    def test_query_only_before_after_generation(self):
        """Test query-only generation creates a visible before/after pair."""
        system = ZeroShotAlignmentSystem()

        result = system.align_response("Explain gradient descent in a technical way.")

        assert result["base_response"]
        assert result["styled_response"]
        assert result["base_response"] != result["original_prompt"]
        assert result["styled_response"] != result["base_response"]
        assert result["base_response_source"] == "auto_generated"
        print("[PASS] test_query_only_before_after_generation")

    def test_user_override_source_and_rewrite(self):
        """Test user override is preserved as the before-alignment response."""
        system = ZeroShotAlignmentSystem()

        result = system.align_response(
            prompt="Make this professional.",
            response="Hey, this thing works pretty well."
        )

        assert result["base_response"] == "Hey, this thing works pretty well."
        assert result["base_response_source"] == "user_override"
        assert result["base_provider"] == "user"
        assert result["styled_response"] != result["base_response"]
        print("[PASS] test_user_override_source_and_rewrite")

    def test_no_api_schema_fallback_still_works(self):
        """Test the always-available schema fallback path."""
        system = ZeroShotAlignmentSystem()

        result = system.align_response("Tell me the weather today")

        assert result["base_response"]
        assert result["styled_response"]
        assert result["base_provider"] == "schema"
        assert result["alignment_provider"] == "schema"
        assert result["base_response"] != result["original_prompt"]
        assert result["styled_response"] != result["base_response"]
        assert "log_file" in result
        print("[PASS] test_no_api_schema_fallback_still_works")

    def test_manual_override_provider_metadata(self):
        """Test manual override uses user base provider and provider stack for alignment."""
        system = ZeroShotAlignmentSystem()

        result = system.align_response(
            prompt="Make this friendly.",
            response="Overall, it is a warm Arizona spring day with higher temperatures in the afternoon.",
        )

        assert result["base_provider"] == "user"
        assert result["base_response_source"] == "user_override"
        assert result["alignment_provider"] in {"github", "gemini", "groq", "ollama", "schema"}
        assert result["styled_response"] != result["base_response"]
        print("[PASS] test_manual_override_provider_metadata")

    def test_provider_chain_recorded(self):
        """Test provider attempts are recorded."""
        system = ZeroShotAlignmentSystem()
        result = system.align_response("Explain machine learning")

        assert "provider_attempts" in result
        assert isinstance(result["provider_attempts"], list)
        assert len(result["provider_attempts"]) >= 1
        print("[PASS] test_provider_chain_recorded")

    def test_log_file_exists(self):
        """Test the configured log file is created."""
        system = ZeroShotAlignmentSystem()
        result = system.align_response("Explain alignment")

        assert Path(result["log_file"]).exists()
        print("[PASS] test_log_file_exists")

    def test_json_safe_scores(self):
        """Test top-k scores are JSON-safe name/float pairs."""
        system = ZeroShotAlignmentSystem()

        result = system.align_response("Explain gradient descent in a technical way.")

        for item in result["top_styles"]:
            assert isinstance(item[0], str)
            assert isinstance(item[1], float)
        print("[PASS] test_json_safe_scores")

    def test_multiple_alignment_calls(self):
        """Test multiple alignment calls with different prompts."""
        system = ZeroShotAlignmentSystem()
        
        test_cases = [
            ("I need business language", "Hello there"),
            ("Be casual with me", "Greetings"),
            ("Technical terms please", "Hi everyone"),
        ]
        
        for prompt, response in test_cases:
            result = system.align_response(prompt, response)
            assert result["best_style"] in system.style_library.list_styles()
        
        print("[PASS] test_multiple_alignment_calls")


def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "="*70)
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    test_classes = [
        TestStyleLibrary,
        TestEmbeddingModule,
        TestRetrievalModule,
        TestStyleApplicator,
        TestZeroShotAlignmentSystem,
    ]
    
    total_tests = 0
    passed_tests = 0
    for test_class in test_classes:
        print(f"\n[{test_class.__name__}]")
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method_name in methods:
            method = getattr(instance, method_name)
            total_tests += 1
            try:
                method()
                passed_tests += 1
            except Exception as e:
                print(f"[FAIL] {method_name}: {e}")
    
    print("\n" + "="*70)
    print(f"TOTAL TESTS PASSED: {passed_tests}/{total_tests}")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_tests()
