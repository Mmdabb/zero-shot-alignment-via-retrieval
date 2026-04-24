"""Retrieval Module - Performs similarity-based style retrieval."""

from typing import List, Tuple, Dict
from .embeddings import EmbeddingModule
from .style_library import Style


class RetrievalModule:
    """Retrieves the most relevant style based on query similarity."""

    def __init__(self, embedding_module: EmbeddingModule):
        """
        Initialize retrieval module.

        Args:
            embedding_module: EmbeddingModule instance for computing similarities
        """
        self.embedding_module = embedding_module
        self.style_embeddings: Dict[str, List[float]] = {}

    def index_styles(self, styles: Dict[str, Style]) -> None:
        """
        Index style descriptions for fast retrieval.

        Args:
            styles: Dictionary of style name to Style object
        """
        for name, style in styles.items():
            combined = f"{style.name}. {style.description}. Examples: {' '.join(style.examples)}"
            self.style_embeddings[name] = self.embedding_module.embed_text(combined)

    def retrieve_top_k(self, query: str, styles: Dict[str, Style], k: int = 1) -> List[Tuple[str, float]]:
        """
        Retrieve top-k styles most similar to query.
        
        Args:
            query: User query
            styles: Dictionary of style name to Style object
            k: Number of top results to return
            
        Returns:
            List of (style_name, similarity_score) tuples
        """
        # Index styles if not already done
        if not self.style_embeddings:
            self.index_styles(styles)
        
        # Embed the query
        query_embedding = self.embedding_module.embed_text(query)
        
        # Compute similarities
        similarities = []
        for style_name, style_embedding in self.style_embeddings.items():
            sim = self.embedding_module.cosine_similarity(query_embedding, style_embedding)
            similarities.append((style_name, sim))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        return similarities[:k]

    def retrieve_single(self, query: str, styles: Dict[str, Style]) -> str:
        """
        Retrieve the single best matching style.
        
        Args:
            query: User query
            styles: Dictionary of style name to Style object
            
        Returns:
            Best matching style name
        """
        results = self.retrieve_top_k(query, styles, k=1)
        if results:
            return results[0][0]
        return "formal"  # default fallback
