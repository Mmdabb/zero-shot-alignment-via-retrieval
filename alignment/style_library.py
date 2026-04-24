"""Style Library Module - Stores predefined style descriptions."""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Style:
    """Represents a communication style."""
    name: str
    description: str
    examples: List[str]


class StyleLibrary:
    """Manages a collection of communication styles."""

    def __init__(self):
        """Initialize the style library with predefined styles."""
        self.styles: Dict[str, Style] = {}
        self._load_default_styles()

    def _load_default_styles(self) -> None:
        """Load default style definitions."""
        self.styles["formal"] = Style(
            name="formal",
            description="Professional, structured, uses formal language and technical terms appropriately",
            examples=[
                "This is a formal inquiry regarding your services.",
                "We hereby propose a comprehensive solution to address your requirements.",
            ]
        )

        self.styles["casual"] = Style(
            name="casual",
            description="Relaxed, conversational, friendly tone with colloquial expressions",
            examples=[
                "Hey, just checking in on this!",
                "So basically, here's what we can do for you.",
            ]
        )

        self.styles["technical"] = Style(
            name="technical",
            description="Precise, uses domain-specific terminology, detailed technical specifications",
            examples=[
                "The API utilizes RESTful architecture with JSON serialization.",
                "Implement a singleton pattern for resource management.",
            ]
        )

        self.styles["friendly"] = Style(
            name="friendly",
            description="Warm, approachable, emphasizes personal connection and understanding",
            examples=[
                "I'd love to help you with this! Let me explain.",
                "Great question! Here's what I'd recommend based on what you said.",
            ]
        )

    def get_style(self, style_name: str) -> Style:
        """Retrieve a style by name."""
        if style_name not in self.styles:
            raise ValueError(f"Style '{style_name}' not found. Available: {list(self.styles.keys())}")
        return self.styles[style_name]

    def list_styles(self) -> List[str]:
        """Return list of available style names."""
        return list(self.styles.keys())

    def get_style_descriptions(self) -> Dict[str, str]:
        """Return all style descriptions."""
        return {name: style.description for name, style in self.styles.items()}
