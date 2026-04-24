# Codex Upgrade Guide: GitHub-First Multi-Provider LLM Stack + Logging + Environment Setup

## Project Goal

Upgrade the Zero-Shot Alignment via Retrieval project into a robust, demo-ready interactive system with:

```text
1. GitHub Models      Primary hosted demo API
2. Gemini API         Stable hosted fallback
3. Groq API           Fast hosted fallback
4. Ollama             Local fallback
5. Schema fallback    Always-available no-API fallback
```

The system should still:

- use semantic retrieval for communication-style selection,
- avoid fine-tuning,
- show before/after alignment clearly,
- run through both terminal tests and Flask UI,
- log all provider decisions and errors to file.

---

## 1. Final Target Architecture

```text
User Query
   ↓
Semantic Style Retrieval
   ↓
Base Response Generation
   ├── GitHub Models
   ├── Gemini
   ├── Groq
   ├── Ollama
   └── Schema fallback
   ↓
Style-Guided Rewriting
   ├── GitHub Models
   ├── Gemini
   ├── Groq
   ├── Ollama
   └── Schema fallback
   ↓
Return structured result to terminal and Flask UI
```

The Flask UI should show:

- user query,
- retrieved style,
- top-k style scores,
- base response before alignment,
- final response after alignment,
- retrieval model,
- base-generation provider,
- alignment provider,
- provider fallback chain,
- log file path.

---

## 2. Provider Priority

Implement this exact default provider order:

```text
github,gemini,groq,ollama,schema
```

Use the environment variable:

```text
LLM_PROVIDER_ORDER=github,gemini,groq,ollama,schema
```

The system should try each provider in order. If one fails, log the failure and move to the next provider.

The schema fallback must always succeed.

---

## 3. Why GitHub Models First?

GitHub Models is a good demo-first provider because it lets developers prototype with many models using GitHub authentication. GitHub documents it as an inference API that can run multiple model families using GitHub credentials. It is also compatible with OpenAI-style chat completions for many models, which makes it easy to integrate into this project.

Use GitHub Models as the primary **demo/prototyping provider**, but keep Gemini and Groq as fallbacks because GitHub Models can have rate limits or model-specific endpoint differences.

---

## 4. Dependencies

Update `requirements.txt`:

```text
flask>=3.0.0
sentence-transformers>=2.2.0
numpy>=1.21.0
python-dotenv>=1.0.0
requests>=2.31.0

# Provider SDKs
openai>=1.0.0
google-genai>=0.6.0
groq>=0.9.0
```

Optional:

```text
pytest>=8.0.0
```

Notes:

- `openai` is used for GitHub Models because GitHub Models supports OpenAI-compatible chat completions.
- `google-genai` is for Gemini.
- `groq` is for Groq.
- `requests` is for Ollama local HTTP calls.
- `python-dotenv` is for loading `.env`.

---

## 5. Environment Files

Create two files:

```text
.env.example
.env
```

Commit `.env.example`.
Do not commit `.env`.

Add `.env` to `.gitignore` if not already present.

### `.env.example`

```text
# =========================================================
# Global LLM settings
# =========================================================

USE_LLM=true
LLM_PROVIDER_ORDER=github,gemini,groq,ollama,schema

# =========================================================
# GitHub Models primary provider
# =========================================================

GITHUB_TOKEN=
GITHUB_MODEL=openai/gpt-4o-mini

# Recommended default endpoint for GitHub Models OpenAI-compatible inference.
# Some older examples use https://models.inference.ai.azure.com.
# Keep this configurable.
GITHUB_MODELS_BASE_URL=https://models.github.ai/inference

# =========================================================
# Gemini fallback provider
# =========================================================

GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash

# =========================================================
# Groq fallback provider
# =========================================================

GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

# =========================================================
# Ollama local fallback provider
# =========================================================

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# =========================================================
# Retrieval model
# =========================================================

EMBEDDING_MODEL=all-MiniLM-L6-v2

# =========================================================
# Logging
# =========================================================

LOG_LEVEL=INFO
LOG_DIR=logs
LOG_FILE=alignment_demo.log
```

### `.env`

The user should copy `.env.example` to `.env` and fill only the keys they have.

Example minimal `.env` for GitHub Models:

```text
USE_LLM=true
LLM_PROVIDER_ORDER=github,gemini,groq,ollama,schema
GITHUB_TOKEN=your_github_pat_here
GITHUB_MODEL=openai/gpt-4o-mini
GITHUB_MODELS_BASE_URL=https://models.github.ai/inference
```

---

## 6. Environment Setup Guideline for the User

Add this to `README.md` or create `ENVIRONMENT_SETUP.md`.

### 6.1 GitHub Models Setup

1. Go to GitHub.
2. Open:

```text
Settings → Developer settings → Personal access tokens
```

3. Create a token with access to GitHub Models.

Recommended:

```text
Fine-grained token
Permission: models:read
```

4. Add it to `.env`:

```text
GITHUB_TOKEN=your_token_here
GITHUB_MODEL=openai/gpt-4o-mini
GITHUB_MODELS_BASE_URL=https://models.github.ai/inference
```

5. Run a quick test:

```bash
python interactive_alignment_test.py
```

Expected provider:

```text
Base Provider: github
Alignment Provider: github
```

If GitHub fails because of rate limits or endpoint/model mismatch, the system should automatically try Gemini, then Groq, then Ollama, then schema.

### 6.2 Gemini Setup

1. Open Google AI Studio.
2. Create an API key.
3. Add to `.env`:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

4. Keep provider order as:

```text
LLM_PROVIDER_ORDER=github,gemini,groq,ollama,schema
```

Gemini should run only if GitHub Models fails or is unavailable.

### 6.3 Groq Setup

1. Create a Groq Cloud account.
2. Generate an API key.
3. Add to `.env`:

```text
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

If this model is unavailable, choose another active Groq chat model and update `.env`.

### 6.4 Ollama Setup

1. Install Ollama.
2. Pull a lightweight model:

```bash
ollama pull llama3.2:3b
```

3. Make sure Ollama is running:

```bash
ollama serve
```

4. Add to `.env`:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

5. If no hosted API keys are available, use:

```text
LLM_PROVIDER_ORDER=ollama,schema
```

### 6.5 Schema Fallback

No setup needed.

This should work even if:

- no internet,
- no API keys,
- no Ollama,
- no local model.

---

## 7. Logging Requirements

Create or update a logging module:

```text
alignment/logging_config.py
```

The system must log to both:

1. console,
2. file.

Default log file:

```text
logs/alignment_demo.log
```

### 7.1 Required Log Events

Log the following events:

```text
System startup
Loaded environment variables
Active provider order
Embedding model selected
Whether SentenceTransformer loaded or fallback embedding is used
User query received
Whether base response was user override or auto-generated
Each provider attempt for base generation
Each provider attempt for alignment generation
Provider success
Provider failure and error message
Final selected base provider
Final selected alignment provider
Retrieved style
Top-k style scores
Flask /align request start and end
Unhandled exceptions with stack trace
```

### 7.2 Logging Format

Use a readable format:

```text
2026-04-24 15:40:21 | INFO | alignment.llm_client | Trying provider=github task=base_generation model=openai/gpt-4o-mini
```

### 7.3 Python Logging Setup

Suggested implementation:

```python
# alignment/logging_config.py

import logging
import os
from pathlib import Path


def setup_logging() -> logging.Logger:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_file = os.getenv("LOG_FILE", "alignment_demo.log")

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))

    # Avoid duplicate handlers in Flask debug reloads.
    if not root.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    return logging.getLogger("alignment")
```

Call this once at app startup and terminal-test startup.

### 7.4 Log File Path in Results

`ZeroShotAlignmentSystem.align_response()` should include:

```python
"log_file": "logs/alignment_demo.log"
```

in the returned result.

The Flask UI should display the log file path.

---

## 8. Files to Modify or Create

Expected structure:

```text
alignment/
├── __init__.py
├── embeddings.py
├── retrieval.py
├── style_library.py
├── style_application.py
├── style_schema.py              NEW
├── fallback_generator.py        NEW
├── prompts.py                   NEW
├── logging_config.py            NEW
├── llm_client.py                REPLACE/REFACTOR
├── providers/                   NEW
│   ├── __init__.py
│   ├── base.py
│   ├── github_provider.py       NEW
│   ├── gemini_provider.py
│   ├── groq_provider.py
│   ├── ollama_provider.py
│   └── schema_provider.py
└── main.py

web_demo/
├── app.py
├── templates/index.html
└── static/
    ├── app.js
    └── style.css

interactive_alignment_test.py
ENVIRONMENT_SETUP.md             NEW
.env.example                     NEW
```

---

## 9. Provider Interface

Create `alignment/providers/base.py`.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderResult:
    text: str
    provider: str
    model: str
    success: bool
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def generate_base_response(self, user_query: str) -> ProviderResult:
        pass

    @abstractmethod
    def generate_aligned_response(
        self,
        user_query: str,
        base_response: str,
        style_name: str,
        style_description: str,
        style_schema: dict,
    ) -> ProviderResult:
        pass
```

---

## 10. GitHub Models Provider

Create:

```text
alignment/providers/github_provider.py
```

### Environment Variables

```text
GITHUB_TOKEN
GITHUB_MODEL
GITHUB_MODELS_BASE_URL
```

Default values:

```python
model = os.getenv("GITHUB_MODEL", "openai/gpt-4o-mini")
base_url = os.getenv("GITHUB_MODELS_BASE_URL", "https://models.github.ai/inference")
```

### Implementation Guidance

Use the OpenAI Python SDK.

```python
import os
from openai import OpenAI
from .base import BaseLLMProvider, ProviderResult


class GitHubModelsProvider(BaseLLMProvider):
    name = "github"

    def __init__(self):
        self.api_key = os.getenv("GITHUB_TOKEN")
        self.model = os.getenv("GITHUB_MODEL", "openai/gpt-4o-mini")
        self.base_url = os.getenv(
            "GITHUB_MODELS_BASE_URL",
            "https://models.github.ai/inference"
        )
        self.client = None

        if self.api_key:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )

    def is_available(self) -> bool:
        return self.client is not None

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
```

Important:

- Catch all exceptions.
- Return `ProviderResult(success=False, error=str(exc))` on failure.
- Log the error.
- Do not stop the pipeline if GitHub fails.

### Endpoint Note

GitHub Models has had examples using both:

```text
https://models.github.ai/inference
https://models.inference.ai.azure.com
```

Keep `GITHUB_MODELS_BASE_URL` configurable so the user can change it without editing code.

---

## 11. Gemini Provider

Create:

```text
alignment/providers/gemini_provider.py
```

Environment:

```text
GEMINI_API_KEY
GEMINI_MODEL
```

Default:

```python
GEMINI_MODEL=gemini-2.5-flash
```

Use `google-genai`.

Provider should:

- return unavailable if `GEMINI_API_KEY` missing,
- catch exceptions,
- log failures,
- return `ProviderResult`.

---

## 12. Groq Provider

Create:

```text
alignment/providers/groq_provider.py
```

Environment:

```text
GROQ_API_KEY
GROQ_MODEL
```

Default:

```python
GROQ_MODEL=llama-3.3-70b-versatile
```

Use the Groq Python SDK.

Provider should:

- return unavailable if `GROQ_API_KEY` missing,
- catch rate-limit errors and model errors,
- log failures,
- return `ProviderResult`.

---

## 13. Ollama Provider

Create:

```text
alignment/providers/ollama_provider.py
```

Environment:

```text
OLLAMA_BASE_URL
OLLAMA_MODEL
```

Default:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

Use local HTTP:

```text
GET  /api/tags
POST /api/chat
```

Provider should:

- return unavailable if Ollama not running,
- catch connection errors,
- log failures,
- return `ProviderResult`.

---

## 14. Schema Provider

Create:

```text
alignment/providers/schema_provider.py
```

This provider:

- is always available,
- calls `fallback_generator.generate_fallback_base_response()`,
- calls `fallback_generator.schema_rewrite()`,
- returns `ProviderResult(success=True)`,
- never raises provider-level exceptions.

---

## 15. Style Schema

Create:

```text
alignment/style_schema.py
```

Use structured style schemas:

```python
STYLE_SCHEMAS = {
    "formal": {
        "tone": ["professional", "polished", "objective"],
        "structure": ["complete sentences", "clear framing", "no slang"],
        "detail_level": "moderate",
        "opening_strategy": "direct and professional",
        "wording": {
            "avoid": ["hey", "yeah", "wanna", "pretty"],
            "prefer": ["regarding", "would like", "therefore", "recommend"]
        },
        "rewrite_goal": "make the response suitable for academic or business communication"
    },
    "casual": {
        "tone": ["relaxed", "conversational", "simple"],
        "structure": ["short sentences", "natural flow"],
        "detail_level": "low to moderate",
        "opening_strategy": "simple and direct",
        "wording": {
            "avoid": ["hereby", "therefore", "utilize"],
            "prefer": ["basically", "pretty much", "you can think of it as"]
        },
        "rewrite_goal": "make the response natural and easygoing"
    },
    "technical": {
        "tone": ["precise", "analytical", "implementation-focused"],
        "structure": ["define concept", "explain mechanism", "mention inputs and outputs"],
        "detail_level": "high",
        "opening_strategy": "technical framing",
        "wording": {
            "avoid": ["thing", "stuff", "kind of"],
            "prefer": ["algorithm", "module", "parameter", "objective", "process"]
        },
        "rewrite_goal": "make the response precise, technical, and implementation-oriented"
    },
    "friendly": {
        "tone": ["warm", "supportive", "approachable"],
        "structure": ["acknowledge", "explain clearly", "end with helpful note"],
        "detail_level": "moderate",
        "opening_strategy": "supportive and reassuring",
        "wording": {
            "avoid": ["cold", "overly formal", "robotic"],
            "prefer": ["sure", "happy to help", "it may help to think of it as"]
        },
        "rewrite_goal": "make the response supportive, clear, and easy to follow"
    }
}
```

---

## 16. Prompt Templates

Create:

```text
alignment/prompts.py
```

### Base Response Prompt

```python
def build_base_response_prompt(user_query: str) -> tuple[str, str]:
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
```

### Aligned Response Prompt

```python
def build_aligned_response_prompt(
    user_query: str,
    base_response: str,
    style_name: str,
    style_description: str,
    style_schema: dict,
) -> tuple[str, str]:
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
```

---

## 17. Domain-Aware Fallback Base Generation

Create:

```text
alignment/fallback_generator.py
```

Implement:

```python
def generate_fallback_base_response(user_query: str) -> str:
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
```

---

## 18. Schema-Based Fallback Rewrite

In `alignment/fallback_generator.py`, also implement:

```python
def schema_rewrite(base_response: str, style_name: str, style_schema: dict) -> str:
    ...
```

Rules:

- Do not just prepend phrases.
- Rewrite sentence wording and structure.
- Preserve meaning.
- Use the style schema.

Example behavior:

### Friendly weather response

Base:

```text
Weather conditions depend on live location and forecast data. A useful answer should describe temperature, sky conditions, wind, and comfort level for the day.
```

Friendly rewrite:

```text
A helpful weather update should tell you the temperature, sky conditions, wind, and how comfortable it will feel during the day. Since weather depends on live local data, the system would need a current forecast source to give exact conditions.
```

### Formal weather response

```text
Weather conditions depend on the user's location and current forecast data. A complete response should report the expected temperature, sky conditions, wind, and overall comfort level for the day.
```

### Technical weather response

```text
A weather response requires real-time location-specific forecast data, including temperature, cloud cover, wind conditions, and perceived comfort metrics.
```

### Casual weather response

```text
To answer that well, the system would need your live local forecast. A useful weather update would cover the temperature, sky conditions, wind, and how it feels outside.
```

---

## 19. LLM Client Provider Manager

Refactor:

```text
alignment/llm_client.py
```

Required class:

```python
class LLMClient:
    def __init__(self):
        self.providers = self._load_providers()

    def generate_base_response(self, user_query: str) -> dict:
        ...

    def generate_aligned_response(
        self,
        user_query: str,
        base_response: str,
        style_name: str,
        style_description: str,
        style_schema: dict,
    ) -> dict:
        ...
```

Return dictionaries:

```python
{
    "text": "...",
    "provider": "github",
    "model": "openai/gpt-4o-mini",
    "success": True,
    "error": None,
    "attempts": [
        {"provider": "github", "success": True, "error": None}
    ]
}
```

If one provider fails, append attempt and try the next.

Log each attempt.

---

## 20. Modify `alignment/main.py`

Update `ZeroShotAlignmentSystem.align_response()` to return:

```python
{
    "original_prompt": prompt,
    "base_response": base_response_text,
    "best_style": best_style,
    "top_styles": top_styles,
    "style_prompt_augmentation": style_prompt,
    "styled_response": aligned_text,

    "base_response_source": "auto_generated" or "user_override",
    "base_provider": "github" or "gemini" or "groq" or "ollama" or "schema" or "user",
    "base_model": "...",
    "alignment_provider": "github" or "gemini" or "groq" or "ollama" or "schema",
    "alignment_model": "...",

    "retrieval_model": self.embedding_module.active_model_name,
    "provider_attempts": [...],
    "log_file": "logs/alignment_demo.log"
}
```

If user provides base response override:

```python
base_provider = "user"
base_model = "manual-override"
```

Still use provider stack for alignment.

---

## 21. Modify `alignment/style_application.py`

Remove old prefix-based fallback logic.

Use `LLMClient.generate_aligned_response()`.

If schema fallback is reached, it should be handled by `SchemaProvider`, not old rule logic.

---

## 22. Modify Flask Backend

Update `/align` to return new metadata.

Also log:

- request received,
- prompt length,
- whether override was provided,
- result provider,
- exceptions.

---

## 23. Modify Flask UI

Show these fields:

```text
Retrieved Style
Top-k Similarity Scores
Before Alignment: Base Response
After Alignment: Final Response
Base Provider / Model
Alignment Provider / Model
Retrieval Model
Provider Attempts
Log File Path
```

For provider attempts, show a compact chain like:

```text
github failed → gemini succeeded
```

---

## 24. Improve Interactive Terminal Test

Update `interactive_alignment_test.py`.

It should print:

```text
User Query:
...

Retrieved Style:
...

Top-k Style Scores:
...

Before Alignment:
...

After Alignment:
...

Retrieval Model:
...

Base Provider:
...

Alignment Provider:
...

Provider Attempts:
- github: failed/succeeded
- gemini: failed/succeeded
- groq: failed/succeeded
- ollama: failed/succeeded
- schema: succeeded

Log File:
logs/alignment_demo.log
```

---

## 25. Acceptance Tests

### Test 1: No API still works

With no API keys and no Ollama running:

```python
result = system.align_response("Tell me the weather today")

assert result["base_response"]
assert result["styled_response"]
assert result["base_provider"] == "schema"
assert result["alignment_provider"] == "schema"
assert result["base_response"] != result["original_prompt"]
assert result["styled_response"] != result["base_response"]
assert "log_file" in result
```

### Test 2: Manual override still works

```python
result = system.align_response(
    prompt="Make this friendly.",
    response="Overall, it is a warm Arizona spring day with higher temperatures in the afternoon."
)

assert result["base_provider"] == "user"
assert result["base_response_source"] == "user_override"
assert result["alignment_provider"] in {"github", "gemini", "groq", "ollama", "schema"}
assert result["styled_response"] != result["base_response"]
```

### Test 3: Provider chain recorded

```python
assert "provider_attempts" in result
assert isinstance(result["provider_attempts"], list)
assert len(result["provider_attempts"]) >= 1
```

### Test 4: Scores are JSON-safe

```python
for item in result["top_styles"]:
    assert isinstance(item[0], str)
    assert isinstance(item[1], float)
```

### Test 5: Log file exists

```python
from pathlib import Path
assert Path(result["log_file"]).exists()
```

---

## 26. Commands That Should Work

From project root:

```bash
pip install -r requirements.txt
python -m alignment.main
python interactive_alignment_test.py
python web_demo/app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 27. Documentation Updates

Update `README.md` with:

```markdown
## Multi-Provider LLM Stack

The system tries providers in this order:

1. GitHub Models
2. Gemini
3. Groq
4. Ollama
5. Schema fallback
```

Also add:

```markdown
## Environment Setup

See ENVIRONMENT_SETUP.md.
```

Also add:

```markdown
## Logging

Runtime logs are saved to `logs/alignment_demo.log`.
```

---

## 28. Report Update

Update `final_report.tex` with a subsection:

```latex
\subsection{Multi-Provider Inference and Schema-Based Fallback}
```

Mention:

- GitHub Models as primary demo provider,
- Gemini and Groq as hosted fallbacks,
- Ollama as local fallback,
- schema fallback as no-API safety layer,
- no fine-tuning,
- provider transparency,
- logs saved for debugging and reproducibility.

---

## 29. Important Constraints

Do not:

- hard-code API keys,
- remove schema fallback,
- require OpenAI direct API,
- require GPU,
- claim live weather data unless a weather API is integrated,
- hide provider failures,
- use prefix-only fallback alignment,
- commit `.env`.

Keep the system:

- modular,
- transparent,
- demo-safe,
- easy to explain.
