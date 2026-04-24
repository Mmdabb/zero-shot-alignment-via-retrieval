# Zero-Shot Alignment via Retrieval

A lightweight, inference-time LLM alignment system that adapts responses to user-preferred communication styles **without fine-tuning**.

## Overview

Modern LLM alignment methods (RLHF, DPO, LoRA) require training and are resource-intensive. This project proposes a **retrieval-based approach** that:

- Maintains a library of communication styles (formal, casual, technical, friendly)
- Encodes user queries and style descriptions using embeddings
- Retrieves the best-matching style via cosine similarity
- Applies the style at inference time via prompt augmentation

This enables **zero-shot, real-time alignment** to diverse user preferences without retraining the model.

## Improved Before/After Alignment Architecture

The demo now separates content generation from alignment. First, the system generates a neutral base response to the user query. Then it retrieves the most appropriate communication style using semantic similarity. Finally, it rewrites the base response using the retrieved style, giving a clear before-and-after comparison.

The base response can be generated automatically, but the interface also allows a manual override so we can test alignment on any input response. If provider credentials are configured, the system tries GitHub Models first, then Gemini, Groq, Ollama, and finally the schema fallback. The schema fallback is always available, so the Flask demo and tests do not crash offline.

```text
User Query
   ->
Generate neutral/plain base response
   ->
Retrieve intended style from user query
   ->
Rewrite base response using retrieved style
   ->
Display before/after in Flask UI
```

## Multi-Provider LLM Stack

The system tries providers in this order by default:

1. GitHub Models
2. Gemini
3. Groq
4. Ollama
5. Schema fallback

Configure the order with:

```text
LLM_PROVIDER_ORDER=github,gemini,groq,ollama,schema
```

Every run records provider attempts, failures, selected models, and the fallback chain in the returned result and runtime logs.

## Key Features

✅ **Zero-Shot Alignment** - No training required, works at inference time  
✅ **Style Retrieval** - Similarity-based style matching via embeddings  
✅ **Prompt Augmentation** - Apply styles through intelligent prompt engineering  
✅ **Multi-Provider Fallback** - GitHub Models, Gemini, Groq, Ollama, then schema fallback  
✅ **Extensible** - Easy to add new styles to the library  
✅ **Fast** - Cosine similarity retrieval is O(n) where n = number of styles  

## Project Structure

```
alignment/
├── __init__.py              # Package initialization
├── style_library.py         # Style definitions and management
├── embeddings.py            # Embedding generation and similarity
├── retrieval.py             # Style retrieval via similarity search
├── style_application.py     # Style application to responses
├── llm_client.py            # Multi-provider manager
├── providers/               # GitHub, Gemini, Groq, Ollama, schema providers
├── style_schema.py          # Structured style schemas
├── fallback_generator.py    # No-API fallback generation
├── logging_config.py        # Console and file logging
└── main.py                  # Complete system and demo

tests/
├── test_alignment.py        # Comprehensive test suite (20+ tests)

data/                        # Placeholder for style examples and evaluation sets
results/                     # Output results and metrics

README.md                    # This file
requirements.txt            # Python dependencies
project_scope.md            # Project scope document
proposal.md                 # Project proposal
```

## Installation

### Prerequisites
- Python 3.8+

### Setup

```bash
# Clone or navigate to project directory
cd KRR_project

# Create virtual environment (optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

See [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) for GitHub Models, Gemini, Groq, Ollama, and schema fallback setup.

Create a `.env` file in the project root with only the keys you have. Minimal GitHub Models example:

```text
LLM_PROVIDER_ORDER=github,gemini,groq,ollama,schema
GITHUB_TOKEN=your_github_pat_here
GITHUB_MODEL=openai/gpt-4o-mini
GITHUB_MODELS_BASE_URL=https://models.github.ai/inference
USE_LLM=true
```

If no API keys or local Ollama server are available, the system automatically uses the schema fallback.

## Logging

Runtime logs are saved to `logs/alignment_demo.log` by default. The log path is included in terminal output, Flask JSON responses, and the web UI.

## Quick Start

### Run the System Demo

```bash
python -m alignment.main
```

This will run a demonstration showing:
- Semantic query-to-style retrieval with SentenceTransformers
- Automatic base response generation
- Style-aligned final responses
- Before Alignment and After Alignment outputs
- Top-4 matching styles with similarity scores

### Run the Test Suite

```bash
python tests/test_alignment.py
```

Runs 20+ comprehensive tests covering:
- Style library management
- Embedding generation and similarity
- Retrieval accuracy
- Style application
- End-to-end system alignment

### Run the Flask Demo

```bash
python web_demo/app.py
```

Then open `http://127.0.0.1:5000`.

The Flask page shows the user query, optional base response override, retrieved style, top-k similarity scores, base response before alignment, final response after alignment, base/alignment provider and model, provider attempts, retrieval model, and log file path.

## System Components

### 1. Style Library (`style_library.py`)

Pre-defined communication styles with descriptions and examples:

```python
from alignment import StyleLibrary

lib = StyleLibrary()
styles = lib.list_styles()
# Output: ['formal', 'casual', 'technical', 'friendly']

style = lib.get_style("formal")
print(style.description)
# Output: Professional, structured, uses formal language and technical terms appropriately
```

**Available Styles:**
- **Formal**: Professional, structured, appropriate technical terminology
- **Casual**: Relaxed, conversational, friendly
- **Technical**: Precise, domain-specific, detailed specifications
- **Friendly**: Warm, approachable, emphasizes connection

### 2. Embeddings Module (`embeddings.py`)

Generates semantic embeddings for text and computes similarity:

```python
from alignment import EmbeddingModule

emb = EmbeddingModule()

# Generate embedding
embedding = emb.embed_text("hello world")

# Compute similarity
similarity = emb.compute_similarity("formal language", "professional tone")
print(f"Similarity: {similarity:.4f}")
```

### 3. Retrieval Module (`retrieval.py`)

Finds the best-matching style for a given query:

```python
from alignment import RetrievalModule, StyleLibrary, EmbeddingModule

lib = StyleLibrary()
emb = EmbeddingModule()
retrieval = RetrievalModule(emb)

# Get single best style
best_style = retrieval.retrieve_single("technical specifications", lib.styles)
print(f"Best style: {best_style}")

# Get top-k styles with scores
top_styles = retrieval.retrieve_top_k("explain casually", lib.styles, k=3)
for name, score in top_styles:
    print(f"{name}: {score:.4f}")
```

### 4. Style Applicator (`style_application.py`)

Applies retrieved styles by rewriting a neutral base response through the provider stack:

```python
from alignment import StyleApplicator, StyleLibrary

lib = StyleLibrary()
applicator = StyleApplicator(lib)

# Create style prompt augmentation
augmented = applicator.augment_prompt(
    "What is machine learning?",
    "formal"
)
# Output: "You MUST respond in a formal tone. Description: Professional... User request: What is machine learning?"

# Apply style to an existing response
styled = applicator.apply_style_to_response(
    "Hi, it's a cool technique",
    "formal"
)
```

### 5. Complete System (`main.py`)

Orchestrates all components:

```python
from alignment import ZeroShotAlignmentSystem

system = ZeroShotAlignmentSystem()

result = system.align_response(prompt="Please explain formally")

print(f"Best Style: {result['best_style']}")
print(f"Before Alignment: {result['base_response']}")
print(f"After Alignment: {result['styled_response']}")
print(f"Base Source: {result['base_response_source']}")
print(f"Top Styles: {result['top_styles']}")
print(f"Base Provider: {result['base_provider']}")
print(f"Alignment Provider: {result['alignment_provider']}")
```

## API Reference

### StyleLibrary

```python
StyleLibrary()
  .list_styles() -> List[str]              # Get all available styles
  .get_style(name: str) -> Style           # Get style details
  .get_style_descriptions() -> Dict        # Get all descriptions
```

### EmbeddingModule

```python
EmbeddingModule(model_name: str = "all-MiniLM-L6-v2", embedding_dim: int = 128)
  .embed_text(text: str) -> List[float]
  .embed_batch(texts: List[str]) -> List[List[float]]
  .cosine_similarity(vec1, vec2) -> float
  .compute_similarity(text1, text2) -> float
```

### RetrievalModule

```python
RetrievalModule(embedding_module: EmbeddingModule)
  .index_styles(styles: Dict)
  .retrieve_top_k(query: str, styles: Dict, k: int) -> List[Tuple[str, float]]
  .retrieve_single(query: str, styles: Dict) -> str
```

### StyleApplicator

```python
StyleApplicator(style_library: StyleLibrary)
  .create_style_prompt(style_name: str) -> str
  .augment_prompt(prompt: str, style_name: str) -> str
  .apply_style_to_response(response: str, style_name: str) -> str
  .generate_aligned_response(user_query: str, base_response: str, style_name: str) -> str
  .get_style_description(style_name: str) -> str
```

### ZeroShotAlignmentSystem

```python
ZeroShotAlignmentSystem()
  .align_response(prompt: str, response: Optional[str] = None) -> Dict
  .demo()
```

`align_response()` returns JSON-friendly before/after fields:

```python
{
    "original_prompt": prompt,
    "base_response": base_response,
    "best_style": best_style,
    "top_styles": top_styles,
    "style_prompt_augmentation": style_prompt,
    "styled_response": styled_response,
    "base_response_source": "auto_generated" or "user_override",
    "base_provider": "github" or "gemini" or "groq" or "ollama" or "schema" or "user",
    "base_model": "...",
    "alignment_provider": "github" or "gemini" or "groq" or "ollama" or "schema",
    "alignment_model": "...",
    "provider_attempts": [...],
    "log_file": "logs/alignment_demo.log",
    "retrieval_model": "all-MiniLM-L6-v2" or fallback model name,
}
```

## Evaluation Metrics

The system is evaluated on:

1. **Retrieval Accuracy** - Does the retrieved style match the query intent?
2. **Style Consistency** - Are augmented responses consistent with the selected style?
3. **Response Quality** - Is the response natural and coherent?
4. **Efficiency** - Constant-time retrieval regardless of style library size

## Design Choices

### Why Embeddings?

Embeddings capture semantic similarity between queries and styles, enabling intuitive style selection based on context rather than keyword matching.

### Why Cosine Similarity?

- Computationally efficient (O(n) for n styles)
- Geometric interpretation: angle between vectors
- Range [0, 1] makes scores interpretable
- Normalized vectors are scale-invariant

### Why Prompt Augmentation?

- Works with any LLM without modifications
- No fine-tuning overhead
- Easily reversible and composable
- Can be layered with other prompting techniques

### Why No Fine-Tuning?

- Reduces training cost and data requirements
- Enables rapid style adaptation
- Scales to arbitrary style preferences
- No catastrophic forgetting

## Future Extensions

- [ ] Add user feedback loop for continuous style refinement
- [ ] Support style interpolation (blending multiple styles)
- [ ] Implement hierarchical style taxonomy
- [ ] Add style intensity control (e.g., "ultra-formal" vs "moderately formal")
- [x] Add hosted and local provider fallbacks beyond a single API
- [ ] Add evaluation against human judgments
- [ ] Extend to code generation and other domains

## Dependencies

- Python 3.8+
- `flask` for the web demo
- `sentence-transformers` for semantic retrieval when model loading is available
- `numpy` for numerical support
- `openai` for GitHub Models OpenAI-compatible chat completions
- `google-genai` for Gemini
- `groq` for Groq
- `requests` for Ollama
- `python-dotenv` for `.env` configuration

## Running Examples

### Example 1: Business Document Alignment

```bash
python -c "
from alignment import ZeroShotAlignmentSystem
system = ZeroShotAlignmentSystem()
result = system.align_response(
    'Generate a professional business email',
    'Hey, wanna meet up?'
)
print(result['styled_response'])
"
```

### Example 2: Technical Documentation

```bash
python -c "
from alignment import ZeroShotAlignmentSystem
system = ZeroShotAlignmentSystem()
result = system.align_response(
    'Explain the system architecture',
    'It works pretty well overall'
)
print(result['styled_response'])
"
```

## Contributing

To add a new style:

```python
# Edit alignment/style_library.py
self.styles['new_style'] = Style(
    name='new_style',
    description='Your style description here',
    examples=['Example 1', 'Example 2']
)
```

## Testing

Run comprehensive tests:

```bash
python tests/test_alignment.py
```

Output will show:
- Test coverage across all modules
- Summary statistics

## Limitations

- SentenceTransformers may need to download model weights on first use; if unavailable, the system uses deterministic keyword embeddings.
- Limited style library (easily extensible)
- Schema fallback response generation is intentionally simple compared with real LLM generation.
- No user feedback mechanism yet


## License

MIT License - See LICENSE file for details

## Authors

KRR Project Group 09

## Questions?

For issues, questions, or suggestions, please refer to the project documentation or contact the development team.

---

**Last Updated**: April 2026  
**Version**: 1.0.0
