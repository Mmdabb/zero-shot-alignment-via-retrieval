# Improvement README for Codex
## Upgrade Zero-Shot Alignment System with Semantic Retrieval and Automatic Response Generation

## 1. Purpose

Revise the current zero-shot alignment project so that it becomes a stronger, more realistic interactive system.

The current implementation has two main limitations:

1. The embedding module uses deterministic hash-based embeddings, which do not capture real semantic meaning.
2. The base response is manually typed by the user instead of being generated automatically.

The goal of this improvement is to upgrade the system so that:

```text
User Query
   ↓
Semantic style retrieval
   ↓
Automatic base response generation
   ↓
Retrieved-style-guided final response
   ↓
Interactive Flask demo
```

The system should still avoid fine-tuning. Alignment should happen at inference time through retrieval and prompt construction.

---

## 2. Current System Summary

Current modules:

```text
alignment/
├── __init__.py
├── style_library.py
├── embeddings.py
├── retrieval.py
├── style_application.py
└── main.py

web_demo/
├── app.py
├── templates/index.html
└── static/
    ├── app.js
    └── style.css
```

Current behavior:

```text
User Query + Manually Typed Base Response
      ↓
Hash-based embedding retrieval
      ↓
Best style selection
      ↓
Rule-based style application
```

Current limitation:

- The retrieval logic is structurally correct, but semantic understanding is weak.
- The base response is simulated by user input.
- Style application is rule-based and shallow.

---

## 3. Target Improved Architecture

Implement the following pipeline:

```text
User Query
   ↓
Semantic Embedding Module
   ↓
Retrieve Best Style
   ↓
Generate Base Response Automatically
   ↓
Generate or Rewrite Final Response Using Retrieved Style
   ↓
Return Result to Flask UI
```

The system should support two modes:

### Mode A: Local / Offline Demo Mode

Use a simple internal generator if no API key is available.

This mode should still run without crashing.

### Mode B: LLM API Mode

If an API key is available, use an LLM API to generate:

1. a neutral/base response, and
2. a final style-aligned response.

---

## 4. Dependencies to Add

Update `requirements.txt`:

```text
flask>=3.0.0
sentence-transformers>=2.2.0
numpy>=1.21.0
openai>=1.0.0
python-dotenv>=1.0.0
```

Notes:

- `sentence-transformers` is used for semantic retrieval.
- `openai` is optional but recommended for real LLM generation.
- `python-dotenv` allows loading the API key from `.env`.

---

## 5. Environment Variables

Add support for `.env`:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
USE_LLM=true
```

If `USE_LLM=false` or no API key exists, the system should fall back to local demo mode.

Do not hard-code API keys.

---

## 6. Files to Modify or Create

### 6.1 Modify `alignment/embeddings.py`

Replace the hash-based embedding approach with SentenceTransformers.

Recommended implementation:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingModule:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str):
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts):
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    @staticmethod
    def cosine_similarity(vec1, vec2):
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / ((np.linalg.norm(v1) * np.linalg.norm(v2)) + 1e-12))

    def compute_similarity(self, text1, text2):
        return self.cosine_similarity(self.embed_text(text1), self.embed_text(text2))
```

Acceptance requirement:

- Similar style-related phrases should have higher similarity than unrelated phrases.
- Example: `professional email` should retrieve `formal`.
- Example: `explain implementation details` should retrieve `technical`.

---

### 6.2 Modify `alignment/retrieval.py`

Keep the current retrieval structure but make sure it works with semantic embeddings.

Important:

- Style representations should combine:
  - style name,
  - description,
  - examples.

Example:

```python
combined = f"{style.name}. {style.description}. Examples: {' '.join(style.examples)}"
```

Return top-k scores as JSON-safe values:

```python
[
  ["formal", 0.82],
  ["technical", 0.61]
]
```

---

### 6.3 Create `alignment/llm_client.py`

Create a new module responsible for LLM calls.

Required behavior:

```python
class LLMClient:
    def __init__(self):
        pass

    def is_available(self) -> bool:
        pass

    def generate_base_response(self, user_query: str) -> str:
        pass

    def generate_aligned_response(
        self,
        user_query: str,
        base_response: str,
        style_name: str,
        style_description: str
    ) -> str:
        pass
```

If OpenAI is available:

- Use the OpenAI Python SDK.
- Generate concise, useful responses.
- Keep temperature low or moderate, e.g. `temperature=0.4`.

If OpenAI is not available:

- Return a simple deterministic fallback response.
- Do not crash.

Fallback example:

```python
return f"This is a neutral base response to the query: {user_query}"
```

---

### 6.4 Modify `alignment/style_application.py`

Currently this module applies shallow rule-based transformations.

Update it so it can support two pathways:

1. Rule-based fallback mode.
2. LLM rewrite mode through `LLMClient`.

Recommended methods:

```python
def create_style_prompt(self, style_name: str) -> str:
    ...

def augment_prompt(self, original_prompt: str, style_name: str) -> str:
    ...

def apply_style_to_response(self, response: str, style_name: str) -> str:
    # fallback rule-based transform
    ...

def generate_aligned_response(self, user_query: str, base_response: str, style_name: str) -> str:
    # use LLMClient if available, otherwise fallback
```

The final aligned response should preserve content but change tone/style.

---

### 6.5 Modify `alignment/main.py`

Revise `ZeroShotAlignmentSystem.align_response()`.

New behavior:

```python
def align_response(self, prompt: str, response: str | None = None) -> dict:
```

Logic:

1. Retrieve best style from `prompt`.
2. Retrieve top-k styles.
3. If `response` is provided and non-empty, use it as the base response.
4. If `response` is missing, automatically generate base response.
5. Generate final aligned response using retrieved style.
6. Return full JSON-friendly result.

Returned dictionary should include:

```python
{
    "original_prompt": prompt,
    "base_response": base_response,
    "best_style": best_style,
    "top_styles": top_styles,
    "style_prompt_augmentation": style_prompt,
    "styled_response": styled_response,
    "generation_mode": "llm" or "fallback",
    "retrieval_model": "all-MiniLM-L6-v2"
}
```

---

### 6.6 Modify `web_demo/app.py`

Update `/align` so the frontend only requires a user query.

Current endpoint expects:

```json
{
  "prompt": "...",
  "response": "..."
}
```

New endpoint should accept:

```json
{
  "prompt": "...",
  "response": "optional..."
}
```

If response is empty, backend should generate the base response automatically.

Return the new result fields:

- `base_response`
- `styled_response`
- `best_style`
- `top_styles`
- `generation_mode`
- `retrieval_model`

---

### 6.7 Modify `web_demo/templates/index.html`

Update the UI to make the pipeline clearer.

Required sections:

1. User Query
2. Optional Base Response
3. Retrieved Style
4. Top-k Scores
5. Auto-generated Base Response
6. Final Aligned Response
7. System Mode

Rename the base response input to:

```text
Optional Base Response Override
```

Add helper text:

```text
Leave this empty to let the system generate the base response automatically.
```

---

### 6.8 Modify `web_demo/static/app.js`

Update frontend logic:

- Send `prompt`.
- Send optional `response` only if provided.
- Display:
  - base response,
  - final aligned response,
  - best style,
  - top-k scores,
  - generation mode,
  - retrieval model.

---

### 6.9 Modify `README.md`

Add a section:

```markdown
## Improved System Architecture
```

Explain:

```text
The original system used hash-based embeddings and manual base responses.
The improved system uses semantic sentence embeddings for style retrieval and optional LLM-based response generation.
```

Add run instructions:

```bash
pip install -r requirements.txt
python web_demo/app.py
```

Add optional `.env` instructions.

---

### 6.10 Modify `final_report.tex`

Add a short subsection:

```latex
\subsection{Improved Semantic Retrieval and Response Generation}
```

Mention:

- Hash embeddings were replaced by semantic sentence embeddings.
- Base response can now be generated automatically.
- Retrieved style is used to guide final response generation.
- No fine-tuning is required.

---

## 7. Preferred Final Pipeline

The recommended final behavior is:

```text
User Query:
"Explain neural networks professionally"

Step 1:
Semantic retrieval selects "formal"

Step 2:
System generates neutral base response:
"Neural networks are computational models inspired by interconnected processing units..."

Step 3:
System generates final aligned response:
"Neural networks are computational models designed to process information through interconnected layers..."
```

---

## 8. Demo Behavior Requirements

The Flask demo should work as follows:

### Case 1: User enters only query

Input:

```text
Explain gradient descent in a technical way.
```

Expected output:

```text
Best style: technical
Base response: generated automatically
Final response: technical explanation
```

### Case 2: User enters query + base response override

Input:

```text
Query: Make this professional.
Base response: Hey, this thing works pretty well.
```

Expected output:

```text
Best style: formal
Final response: formal rewrite of the base response
```

---

## 9. Suggested Evaluation Examples

Add or test the following:

```python
examples = [
    ("Write a professional email to a professor", "formal"),
    ("Explain the algorithm and implementation details", "technical"),
    ("Can you explain this like a friend?", "friendly"),
    ("Tell me casually what this project does", "casual"),
]
```

Expected:

- At least 3 out of 4 should retrieve the intended style using SentenceTransformers.

---

## 10. Acceptance Tests

After Codex modifies the project, these commands should work:

```bash
python -m alignment.main
python tests/test_alignment.py
python web_demo/app.py
```

Manual browser test:

```text
http://127.0.0.1:5000
```

The demo should:

- accept a query,
- retrieve a style,
- generate or accept a base response,
- produce a final aligned response,
- show top-k style scores,
- not crash if no OpenAI key is available.

---

## 11. Important Design Constraints

Do not fine-tune any model.

Do not require GPU.

Do not hard-code secrets.

Do not remove the fallback mode.

Keep the code modular.

Keep the existing class names if possible:

```python
StyleLibrary
EmbeddingModule
RetrievalModule
StyleApplicator
ZeroShotAlignmentSystem
```

---

## 12. Suggested Presentation Explanation

Use this wording:

> The improved system replaces the original hash-based embeddings with semantic sentence embeddings. The user query is used to retrieve the closest communication style, and the system then generates or rewrites the response using the retrieved style. This gives us inference-time alignment without fine-tuning.

Another useful sentence:

> The web demo is not a separate implementation. It calls the same Python modules used by the project and displays the retrieved style, similarity scores, base response, and final aligned response.

---

## 13. Final Expected Output

After implementation, the project should support:

```text
User Query Only
      ↓
Semantic Style Retrieval
      ↓
Automatic Base Response Generation
      ↓
Style-Guided Final Response
      ↓
Interactive Flask Display
```

This will make the project stronger, more realistic, and easier to defend during the final presentation.
