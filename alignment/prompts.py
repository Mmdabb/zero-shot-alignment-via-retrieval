"""Prompt builders for base generation and style-guided rewriting."""


def build_base_response_prompt(user_query: str) -> tuple[str, str]:
    """Build a neutral base-response prompt."""
    system_prompt = "You generate neutral base responses for later style alignment."
    user_prompt = f"""
Answer the user's query in a plain, neutral, concise way.
Do not intentionally use a formal, casual, technical, or friendly tone.
Do not mention that this is a base response.
Do not simply repeat the user query.
If the query asks for current, real-time, or location-specific information that you cannot know, give a safe general response and mention that live data may be needed.

User query:
{user_query}
""".strip()
    return system_prompt, user_prompt


def build_aligned_response_prompt(
    user_query: str,
    base_response: str,
    style_name: str,
    style_description: str,
    style_schema: dict,
) -> tuple[str, str]:
    """Build a style-guided rewrite prompt."""
    system_prompt = "You rewrite responses while preserving meaning."
    user_prompt = f"""
Rewrite the base response using the retrieved communication style.

Preserve the core meaning and factual content.
Do not add unrelated information.
Do not invent live facts.
Change tone, wording, structure, and level of detail according to the style schema.

User query:
{user_query}

Retrieved style:
{style_name}

Style description:
{style_description}

Style schema:
{style_schema}

Base response:
{base_response}

Final aligned response:
""".strip()
    return system_prompt, user_prompt
