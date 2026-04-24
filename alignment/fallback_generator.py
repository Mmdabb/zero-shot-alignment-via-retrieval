"""Always-available fallback generation based on simple schemas."""


def generate_fallback_base_response(user_query: str) -> str:
    """Generate a domain-aware neutral base response without any API."""
    q = user_query.lower()

    if "weather" in q or "temperature" in q or "forecast" in q:
        return (
            "Weather conditions depend on live location and forecast data. "
            "A useful answer should describe temperature, sky conditions, wind, and comfort level for the day."
        )

    if "email" in q or "professor" in q or "meeting" in q:
        return (
            "The message should clearly state the purpose, ask for availability or a response, "
            "and keep the request concise."
        )

    if "gradient descent" in q:
        return (
            "Gradient descent is a method used to improve a model by gradually adjusting its parameters "
            "to reduce error."
        )

    if "neural network" in q or "neural networks" in q:
        return (
            "A neural network is a model that learns patterns from data using connected layers of simple processing units."
        )

    if "machine learning" in q:
        return (
            "Machine learning is a way for computers to learn patterns from data and use them to make predictions or decisions."
        )

    if "alignment" in q or "llm" in q:
        return (
            "Alignment is the process of making a model's output better match user preferences, instructions, or expectations."
        )

    if "project" in q or "system" in q:
        return (
            "The project retrieves a communication style from the user query and uses it to guide the final response."
        )

    return (
        "The user's request can be answered by identifying the main topic, explaining the key idea, "
        "and presenting the information clearly."
    )


def _replace_words(text: str, replacements: dict[str, str]) -> str:
    rewritten = text
    for source, target in replacements.items():
        rewritten = rewritten.replace(source, target)
        rewritten = rewritten.replace(source.capitalize(), target.capitalize())
    return rewritten


def schema_rewrite(base_response: str, style_name: str, style_schema: dict) -> str:
    """Rewrite a base response using deterministic style-schema rules."""
    text = " ".join(base_response.strip().split())
    if not text:
        return text

    lower = text.lower()
    is_weather = "weather" in lower or "forecast" in lower or "temperature" in lower

    if is_weather and style_name == "friendly":
        return (
            "A helpful weather update should tell you the temperature, sky conditions, wind, "
            "and how comfortable it will feel during the day. Since weather depends on live local data, "
            "the system would need a current forecast source to give exact conditions."
        )
    if is_weather and style_name == "formal":
        return (
            "Weather conditions depend on the user's location and current forecast data. "
            "A complete response should report the expected temperature, sky conditions, wind, "
            "and overall comfort level for the day."
        )
    if is_weather and style_name == "technical":
        return (
            "A weather response requires real-time location-specific forecast data, including temperature, "
            "cloud cover, wind conditions, and perceived comfort metrics."
        )
    if is_weather and style_name == "casual":
        return (
            "To answer that well, the system would need your live local forecast. "
            "A useful weather update would cover the temperature, sky conditions, wind, and how it feels outside."
        )

    if style_name == "formal":
        rewritten = _replace_words(
            text,
            {
                "Hey": "Hello",
                "hey": "hello",
                "wanna": "would like to",
                "pretty": "rather",
                "thing": "matter",
                "stuff": "information",
            },
        )
        if not rewritten.endswith("."):
            rewritten += "."
        return f"Regarding this request, {rewritten[0].lower() + rewritten[1:]}"

    if style_name == "casual":
        rewritten = _replace_words(
            text,
            {
                "utilize": "use",
                "therefore": "so",
                "regarding": "about",
                "parameters": "settings",
            },
        )
        return f"Basically, {rewritten[0].lower() + rewritten[1:]}"

    if style_name == "technical":
        rewritten = _replace_words(
            text,
            {
                "thing": "component",
                "stuff": "data",
                "way": "method",
                "helps": "supports",
            },
        )
        return (
            f"Technically, {rewritten[0].lower() + rewritten[1:]} "
            "The key mechanism is to preserve the input meaning while adjusting the output structure and terminology."
        )

    if style_name == "friendly":
        rewritten = _replace_words(
            text,
            {
                "must": "can",
                "requires": "needs",
                "error": "issue",
            },
        )
        return (
            f"Sure, happy to help. {rewritten} "
            "It may help to think of this as a clear, step-by-step explanation shaped for the reader."
        )

    goal = style_schema.get("rewrite_goal", "make the response clearer")
    return f"{text} This rewrite aims to {goal}."
