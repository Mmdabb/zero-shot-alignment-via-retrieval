"""Embeddings Module - Generates embeddings for text."""

import logging
import os
from typing import List

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class EmbeddingModule:
    """Generates semantic embeddings for text.

    SentenceTransformers is used when available. If the model cannot be loaded,
    the module falls back to a deterministic keyword embedding so the demo and
    tests still work offline without downloading model weights.
    """

    def __init__(self, model_name: str = None, embedding_dim: int = 128):
        """
        Initialize embedding module.

        Args:
            model_name: SentenceTransformers model name
            embedding_dim: Fallback embedding dimension for offline mode
        """
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_dim = embedding_dim
        self.model = self._load_model()
        self.active_model_name = self.model_name if self.model is not None else f"fallback-keyword-{embedding_dim}"
        logger.info("Embedding model selected: %s", self.model_name)
        logger.info(
            "SentenceTransformer loaded=%s active_model=%s",
            self.model is not None,
            self.active_model_name,
        )
        self._keyword_groups = [
            {"formal", "professional", "business", "email", "professor", "letter", "polite", "structured", "official"},
            {"casual", "relaxed", "conversation", "conversational", "chat", "informal", "colloquial", "simple"},
            {"technical", "algorithm", "implementation", "architecture", "system", "api", "specification", "details", "neural", "gradient"},
            {"friendly", "friend", "warm", "approachable", "help", "supportive", "kind", "encouraging", "personal"},
        ]

    def _load_model(self):
        if SentenceTransformer is None:
            return None

        try:
            return SentenceTransformer(self.model_name)
        except Exception:
            return None

    def _fallback_embed(self, text: str) -> List[float]:
        normalized = text.lower().strip()
        tokens = normalized.replace("-", " ").replace("_", " ").split()
        token_set = set(tokens)
        embedding = [0.0 for _ in range(self.embedding_dim)]

        for index, keywords in enumerate(self._keyword_groups):
            matches = sum(1 for keyword in keywords if keyword in token_set or keyword in normalized)
            embedding[index] = float(matches)

        for token in tokens:
            bucket = 4 + (sum(ord(ch) for ch in token) % max(self.embedding_dim - 4, 1))
            embedding[bucket] += 0.1

        norm = sum(value ** 2 for value in embedding) ** 0.5
        if norm == 0:
            return embedding
        return [value / norm for value in embedding]

    def _normalize_embedding(self, vector) -> List[float]:
        if hasattr(vector, "tolist"):
            return [float(x) for x in vector.tolist()]
        return [float(x) for x in vector]

    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.model is not None:
            encoded = self.model.encode(text, normalize_embeddings=True)
            return self._normalize_embedding(encoded)
        return self._fallback_embed(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        if self.model is not None:
            encoded = self.model.encode(texts, normalize_embeddings=True)
            return [self._normalize_embedding(vec) for vec in encoded]
        return [self._fallback_embed(text) for text in texts]

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score
        """
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a ** 2 for a in vec1) ** 0.5
        norm2 = sum(b ** 2 for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two pieces of text.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score
        """
        emb1 = self.embed_text(text1)
        emb2 = self.embed_text(text2)
        return self.cosine_similarity(emb1, emb2)
