"""Zero-Shot Alignment via Retrieval - Core Package"""

from .style_library import StyleLibrary
from .embeddings import EmbeddingModule
from .llm_client import LLMClient
from .retrieval import RetrievalModule
from .style_application import StyleApplicator

__version__ = "1.0.0"
__all__ = [
    "StyleLibrary",
    "EmbeddingModule",
    "LLMClient",
    "RetrievalModule",
    "StyleApplicator",
    "ZeroShotAlignmentSystem",
]


def __getattr__(name):
    if name == "ZeroShotAlignmentSystem":
        from .main import ZeroShotAlignmentSystem

        return ZeroShotAlignmentSystem
    raise AttributeError(f"module 'alignment' has no attribute {name!r}")
