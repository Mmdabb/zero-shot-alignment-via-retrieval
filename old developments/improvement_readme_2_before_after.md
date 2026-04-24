# Improvement README 2 for Codex
## Fix Before/After Alignment Flow with Neutral Base Generation and Style-Guided Rewriting

## 1. Purpose

Revise the project so the demo clearly shows the effect of alignment.

The current issue is that the base response is sometimes too close to the user query or simply repeats it. This makes the demo look weak because there is no clear difference between:

1. the response before alignment, and
2. the response after alignment.

The goal of this improvement is to implement a clear before/after pipeline:

```text
User Query
   ↓
Generate neutral/plain base response
   ↓
Retrieve intended style from user query
   ↓
Rewrite base response using retrieved style
   ↓
Display both before and after in Flask UI
```

This should make the demo conceptually stronger and easier to explain.

---

## 2. Desired Final Behavior

The system should support this workflow:

### Case 1: User provides only a query

Input:

```text
Explain gradient descent in a technical way.
```

System should:

1. Generate a neutral base response first.
2. Retrieve the target style from the query.
3. Rewrite the base response using the retrieved style.
4. Display both the base response and aligned response.

Example output:

```text
Retrieved style:
technical

Base response before alignment:
Gradient descent is a method for improving a model by repeatedly adjusting its parameters.

Final response after alignment:
Gradient descent is an iterative optimization algorithm that updates model parameters in the negative direction of the objective-function gradient to minimize loss.
```

---

### Case 2: User provides query + optional base response override

Input:

```text
Query:
Make this sound professional.

Base response override:
Hey, this thing works pretty well and should be useful.
```

System should:

1. Use the provided base response as the before-alignment text.
2. Retrieve style from the query.
3. Rewrite the base response using the retrieved style.

Example output:

```text
Retrieved style:
formal

Base response before alignment:
Hey, this thing works pretty well and should be useful.

Final response after alignment:
This system performs effectively and is expected to provide practical value.
```

---

## 3. Important Conceptual Rule

Do NOT copy the user query into the base response.

The base response should be a neutral answer to the query, not a restatement of the query.

Bad fallback:

```text
This is a neutral base response to the query: Explain gradient descent in a technical way.
```

Better fallback:

```text
Gradient descent is a method used to improve a model by gradually changing its parameters to reduce error.
```

The fallback does not need to be perfect, but it should look like an answer.

---

## 4. Target Pipeline

Implement this pipeline inside `ZeroShotAlignmentSystem.align_response()`:

```python
def align_response(self, prompt: str, response: str | None = None) -> dict:
    # 1. Retrieve best style from prompt
    # 2. If response is provided, use it as base response
    # 3. If response is empty, generate neutral base response
    # 4. Rewrite base response using retrieved style
    # 5. Return before/after fields
```

Required return fields:

```python
{
    "original_prompt": prompt,
    "base_response": base_response,
    "best_style": best_style,
    "top_styles": top_styles,
    "style_prompt_augmentation": style_prompt,
    "styled_response": styled_response,
    "generation_mode": "llm" or "fallback",
    "base_response_source": "auto_generated" or "user_override",
    "retrieval_model": "all-MiniLM-L6-v2"
}
```

---

## 5. LLM-Based Implementation

If an OpenAI API key is available and `USE_LLM=true`, use two LLM calls.

### Call 1: Generate Neutral Base Response

Prompt:

```text
You are generating a neutral base response for later style alignment.

Answer the user's query in a plain, neutral, concise way.
Do not intentionally use a formal, casual, technical, or friendly style.
Do not mention that this is a base response.
Do not simply repeat the user query.

User query:
{user_query}
```

Expected output:

```text
Gradient descent is a method for improving a model by adjusting its parameters to reduce error.
```

---

### Call 2: Rewrite Using Retrieved Style

Prompt:

```text
Rewrite the base response using the requested communication style.

Preserve the core meaning and factual content.
Change only tone, wording, structure, and level of detail as needed.
Do not add unrelated new information.

User query:
{user_query}

Retrieved style:
{style_name}

Style description:
{style_description}

Base response:
{base_response}

Final aligned response:
```

Expected output:

```text
Gradient descent is an iterative optimization method that updates parameters in the direction that reduces the loss function.
```

---

## 6. Fallback Implementation Without API Key

If no API key is available, do not crash.

Implement a deterministic fallback that creates a simple neutral answer.

A better fallback can use keyword templates.

Suggested function:

```python
def generate_fallback_base_response(user_query: str) -> str:
    q = user_query.lower()

    if "gradient descent" in q:
        return "Gradient descent is a method used to improve a model by gradually changing its parameters to reduce error."

    if "neural network" in q or "neural networks" in q:
        return "A neural network is a model that learns patterns from data using connected layers of simple processing units."

    if "machine learning" in q:
        return "Machine learning is a way for computers to learn patterns from data and use them to make predictions or decisions."

    if "alignment" in q:
        return "Alignment is the process of making a system's output better match user expectations or preferences."

    if "email" in q:
        return "The message explains the request clearly and asks for a response or meeting."

    return "The topic can be explained as a process or idea that helps solve the user's request in a clear way."
```

This is acceptable for fallback mode because it avoids simply repeating the query.

---

## 7. Modify `alignment/llm_client.py`

Make sure `LLMClient` has these methods:

```python
class LLMClient:
    def is_available(self) -> bool:
        ...

    def generate_base_response(self, user_query: str) -> str:
        # LLM call if available
        # fallback otherwise
        ...

    def generate_aligned_response(
        self,
        user_query: str,
        base_response: str,
        style_name: str,
        style_description: str
    ) -> str:
        # LLM rewrite if available
        # fallback style transformation otherwise
        ...
```

The fallback aligned response should be better than simple prefixes.

Suggested fallback style transformations:

```python
def fallback_rewrite(base_response: str, style_name: str) -> str:
    if style_name == "formal":
        return (
            "In professional terms, " +
            base_response[0].lower() + base_response[1:]
        )

    if style_name == "technical":
        return (
            "From a technical perspective, " +
            base_response[0].lower() + base_response[1:] +
            " This can be described in terms of system behavior, inputs, and outputs."
        )

    if style_name == "casual":
        return (
            "Basically, " +
            base_response[0].lower() + base_response[1:]
        )

    if style_name == "friendly":
        return (
            "Sure, I can explain it clearly. " +
            base_response
        )

    return base_response
```

---

## 8. Modify `alignment/style_application.py`

This module should not be the only place doing shallow transformations anymore.

It should either:

1. call `LLMClient.generate_aligned_response()`, or
2. provide fallback rewriting when LLM is unavailable.

Recommended structure:

```python
class StyleApplicator:
    def __init__(self, style_library, llm_client=None):
        self.style_library = style_library
        self.llm_client = llm_client

    def create_style_prompt(self, style_name: str) -> str:
        ...

    def generate_aligned_response(self, user_query: str, base_response: str, style_name: str) -> str:
        style = self.style_library.get_style(style_name)

        if self.llm_client and self.llm_client.is_available():
            return self.llm_client.generate_aligned_response(
                user_query=user_query,
                base_response=base_response,
                style_name=style_name,
                style_description=style.description
            )

        return self.apply_style_to_response(base_response, style_name)
```

---

## 9. Modify `alignment/main.py`

`ZeroShotAlignmentSystem` should initialize:

```python
self.llm_client = LLMClient()
self.style_applicator = StyleApplicator(self.style_library, self.llm_client)
```

Then `align_response()` should:

```python
def align_response(self, prompt: str, response: str | None = None) -> dict:
    best_style = self.retrieval_module.retrieve_single(prompt, self.style_library.styles)
    top_styles = self.retrieval_module.retrieve_top_k(prompt, self.style_library.styles, k=4)

    if response and response.strip():
        base_response = response.strip()
        base_response_source = "user_override"
    else:
        base_response = self.llm_client.generate_base_response(prompt)
        base_response_source = "auto_generated"

    styled_response = self.style_applicator.generate_aligned_response(
        user_query=prompt,
        base_response=base_response,
        style_name=best_style
    )

    return {
        "original_prompt": prompt,
        "base_response": base_response,
        "best_style": best_style,
        "top_styles": top_styles,
        "style_prompt_augmentation": self.style_applicator.create_style_prompt(best_style),
        "styled_response": styled_response,
        "generation_mode": "llm" if self.llm_client.is_available() else "fallback",
        "base_response_source": base_response_source,
        "retrieval_model": getattr(self.embedding_module, "model_name", "unknown")
    }
```

---

## 10. Modify Flask UI

Update the UI so the before/after structure is visually clear.

Required sections:

### Input side

```text
User Query
Optional Base Response Override
[Run Alignment]
```

Helper text under optional base response:

```text
Leave this empty to let the system generate a neutral base response automatically.
```

### Output side

Display:

```text
Retrieved Style
Top-k Similarity Scores
Base Response Before Alignment
Final Response After Alignment
Generation Mode
Base Response Source
Retrieval Model
```

The labels should clearly say:

- "Before Alignment"
- "After Alignment"

This is important for presentation.

---

## 11. Modify `web_demo/static/app.js`

The frontend should:

1. Send `prompt`.
2. Send `response` only if the override box is not empty.
3. Display `base_response`.
4. Display `styled_response`.
5. Display `base_response_source`.
6. Display `generation_mode`.
7. Display `retrieval_model`.

Expected JSON response:

```json
{
  "original_prompt": "...",
  "base_response": "...",
  "best_style": "technical",
  "top_styles": [["technical", 0.82], ["formal", 0.61]],
  "style_prompt_augmentation": "...",
  "styled_response": "...",
  "generation_mode": "llm",
  "base_response_source": "auto_generated",
  "retrieval_model": "all-MiniLM-L6-v2"
}
```

---

## 12. Improve Demo Examples

Add example buttons in the UI:

1. Formal email
2. Technical explanation
3. Casual explanation
4. Friendly explanation

Example values:

```javascript
const examples = {
  formal: {
    prompt: "Write a professional email asking a professor for a meeting.",
    response: ""
  },
  technical: {
    prompt: "Explain gradient descent in a technical way.",
    response: ""
  },
  casual: {
    prompt: "Tell me casually what this project does.",
    response: ""
  },
  friendly: {
    prompt: "Explain machine learning like a supportive friend.",
    response: ""
  }
};
```

Leave response empty so auto-generation is demonstrated.

---

## 13. Testing Requirements

After changes, these tests should pass:

### Test 1: Query-only generation

```python
system = ZeroShotAlignmentSystem()
result = system.align_response("Explain gradient descent in a technical way.")

assert result["base_response"]
assert result["styled_response"]
assert result["base_response"] != result["original_prompt"]
assert result["styled_response"] != result["base_response"]
assert result["base_response_source"] == "auto_generated"
```

### Test 2: User override

```python
result = system.align_response(
    prompt="Make this professional.",
    response="Hey, this thing works pretty well."
)

assert result["base_response"] == "Hey, this thing works pretty well."
assert result["base_response_source"] == "user_override"
assert result["styled_response"] != result["base_response"]
```

### Test 3: JSON-safe scores

```python
for item in result["top_styles"]:
    assert isinstance(item[0], str)
    assert isinstance(item[1], float)
```

---

## 14. What NOT to Do

Do not:

- copy the query as the base response,
- hide the base response from the UI,
- remove the optional override box,
- require an API key to run,
- crash if no API key exists,
- claim fine-tuning is being performed,
- remove the retrieval step.

---

## 15. Presentation Explanation

Use this wording:

> The improved demo separates content generation from alignment. First, the system generates a neutral base response to the user query. Then it retrieves the most appropriate communication style using semantic similarity. Finally, it rewrites the base response using the retrieved style, giving a clear before-and-after comparison.

Also say:

> The base response can be generated automatically, but the interface also allows a manual override so we can test alignment on any input response.

---

## 16. Final Expected Result

The Flask demo should clearly show:

```text
User Query:
Explain gradient descent in a technical way.

Retrieved Style:
technical

Before Alignment:
Gradient descent is a method used to improve a model by gradually changing its parameters to reduce error.

After Alignment:
From a technical perspective, gradient descent is an iterative optimization algorithm that updates model parameters in the direction that minimizes the loss function.
```

This makes the alignment contribution visible and defensible.
