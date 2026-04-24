"""Structured communication-style schemas."""

STYLE_SCHEMAS = {
    "formal": {
        "tone": ["professional", "polished", "objective"],
        "structure": ["complete sentences", "clear framing", "no slang"],
        "detail_level": "moderate",
        "opening_strategy": "direct and professional",
        "wording": {
            "avoid": ["hey", "yeah", "wanna", "pretty"],
            "prefer": ["regarding", "would like", "therefore", "recommend"],
        },
        "rewrite_goal": "make the response suitable for academic or business communication",
    },
    "casual": {
        "tone": ["relaxed", "conversational", "simple"],
        "structure": ["short sentences", "natural flow"],
        "detail_level": "low to moderate",
        "opening_strategy": "simple and direct",
        "wording": {
            "avoid": ["hereby", "therefore", "utilize"],
            "prefer": ["basically", "pretty much", "you can think of it as"],
        },
        "rewrite_goal": "make the response natural and easygoing",
    },
    "technical": {
        "tone": ["precise", "analytical", "implementation-focused"],
        "structure": ["define concept", "explain mechanism", "mention inputs and outputs"],
        "detail_level": "high",
        "opening_strategy": "technical framing",
        "wording": {
            "avoid": ["thing", "stuff", "kind of"],
            "prefer": ["algorithm", "module", "parameter", "objective", "process"],
        },
        "rewrite_goal": "make the response precise, technical, and implementation-oriented",
    },
    "friendly": {
        "tone": ["warm", "supportive", "approachable"],
        "structure": ["acknowledge", "explain clearly", "end with helpful note"],
        "detail_level": "moderate",
        "opening_strategy": "supportive and reassuring",
        "wording": {
            "avoid": ["cold", "overly formal", "robotic"],
            "prefer": ["sure", "happy to help", "it may help to think of it as"],
        },
        "rewrite_goal": "make the response supportive, clear, and easy to follow",
    },
}


def get_style_schema(style_name: str) -> dict:
    """Return a style schema, falling back to formal when unknown."""
    return STYLE_SCHEMAS.get(style_name, STYLE_SCHEMAS["formal"])
