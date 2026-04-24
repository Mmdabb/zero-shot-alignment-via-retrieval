# Environment Setup

Copy `.env.example` to `.env` and fill in only the providers you want to use. The default provider order is:

```text
github,gemini,groq,ollama,schema
```

## GitHub Models Setup

1. In GitHub, open `Settings -> Developer settings -> Personal access tokens`.
2. Create a token with access to GitHub Models. A fine-grained token with `models:read` is recommended.
3. Add these values to `.env`:

```text
GITHUB_TOKEN=your_token_here
GITHUB_MODEL=openai/gpt-4o-mini
GITHUB_MODELS_BASE_URL=https://models.github.ai/inference
```

Run:

```bash
python interactive_alignment_test.py
```

Expected provider when configured correctly:

```text
Base Provider: github
Alignment Provider: github
```

If GitHub Models fails because of rate limits or endpoint/model differences, the system automatically tries Gemini, Groq, Ollama, then the schema fallback.

## Gemini Setup

1. Open Google AI Studio.
2. Create an API key.
3. Add to `.env`:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## Groq Setup

1. Create a Groq Cloud account.
2. Generate an API key.
3. Add to `.env`:

```text
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

If this model is unavailable, choose another active Groq chat model and update `.env`.

## Ollama Setup

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

If no hosted API keys are available, use:

```text
LLM_PROVIDER_ORDER=ollama,schema
```

## Schema Fallback

No setup is required. The schema fallback works without internet, API keys, Ollama, or local model weights.
