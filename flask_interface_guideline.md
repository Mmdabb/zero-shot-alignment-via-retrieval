# Flask Web Interface Guideline  
## Interactive Demo for Zero-Shot Alignment via Retrieval

This guideline explains how to create a professional interactive demo for the project using **Flask + HTML/CSS/JavaScript**.

The key idea is:

```text
Browser interface
      ↓
Flask backend
      ↓
Your actual Python alignment code
      ↓
JSON result returned to browser
```

This is different from a static HTML demo. The webpage does **not** fake the model logic. It sends the query to a Python backend, and the backend imports and runs your actual project modules.

---

## 1. Why Flask Is a Good Choice

Flask is a lightweight Python web framework. For this project, it is a good fit because:

- It can directly import your existing Python package.
- It is simple enough for a class demo.
- It lets you build a clean browser interface.
- It keeps the actual system logic in Python.
- It is easier than building a full React/FastAPI production app.

For your presentation, you can say:

> The web interface is only the frontend. When the user submits a query, the Flask backend calls our actual Python alignment system and returns the retrieved style, similarity scores, generated base response, final aligned response, generation mode, retrieval model, and style prompt.

---

## 2. Recommended Project Structure

Place the `web_demo` folder inside your project root:

```text
KRR_project/
├── alignment/
│   ├── __init__.py
│   ├── main.py
│   ├── style_library.py
│   ├── embeddings.py
│   ├── retrieval.py
│   └── style_application.py
│
├── tests/
│   └── test_alignment.py
│
├── web_demo/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── app.js
│
├── README.md
├── requirements.txt
└── flask_interface_guideline.md
```

---

## 3. Files Created for the Interface

### `web_demo/app.py`

This is the Flask backend.

Responsibilities:

1. Load your actual `ZeroShotAlignmentSystem`.
2. Serve the webpage.
3. Receive a query and optional base response override from the browser.
4. Run:

```python
system.align_response(prompt=query, response=base_response)
```

5. Return the result as JSON.

---

### `web_demo/templates/index.html`

This is the user interface.

It includes:

- Query input box
- Optional base response override input box
- Run button
- Best style display
- Top-k style scores
- Auto-generated base response display
- Final aligned response display
- System mode and retrieval model display
- Style prompt augmentation display

---

### `web_demo/static/app.js`

This is the browser-side logic.

Responsibilities:

1. Read user inputs.
2. Send them to the Flask `/align` endpoint.
3. Receive JSON results.
4. Update the page dynamically.

---

### `web_demo/static/style.css`

This controls the visual appearance of the demo.

---

## 4. Installation

From your project root:

```bash
pip install -r requirements.txt
```

The demo uses the same dependency file as the core project:

```text
flask>=3.0.0
sentence-transformers>=2.2.0
numpy>=1.21.0
openai>=1.0.0
python-dotenv>=1.0.0
```

---

## 5. Running the Demo

From the project root:

```bash
python web_demo/app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

## 6. How the Request Flow Works

When you click **Run Alignment**:

```text
index.html/app.js
      ↓ POST /align
web_demo/app.py
      ↓ imports ZeroShotAlignmentSystem
alignment/main.py
      ↓ retrieval + style application
JSON response
      ↓
HTML page updates
```

The returned JSON contains:

```json
{
  "original_prompt": "...",
  "base_response": "...",
  "best_style": "...",
  "top_styles": [["technical", 0.51], ["formal", 0.23]],
  "style_prompt_augmentation": "...",
  "styled_response": "...",
  "generation_mode": "fallback",
  "retrieval_model": "all-MiniLM-L6-v2"
}
```

---

## 7. Why This Is Academically Honest

This is a real system demo because:

- The Python backend is running.
- The backend imports your actual alignment package.
- Retrieval is performed by your actual `RetrievalModule`.
- Embedding generation is performed by your actual `EmbeddingModule`.
- Style application is performed by your actual `StyleApplicator`.

The HTML/JS frontend is only a user interface.

---

## 8. Suggested Presentation Wording

Use this sentence:

> This interactive demo uses a Flask frontend/backend setup. The browser sends the user query to the Python backend, and the backend runs our actual zero-shot alignment system, including style retrieval and response alignment.

Another strong sentence:

> The frontend is not a separate implementation. It calls the same Python modules used in our tests and report.

---

## 9. Common Issues and Fixes

### Issue: `ModuleNotFoundError: No module named 'alignment'`

Make sure you run the command from the project root:

```bash
cd KRR_project
python web_demo/app.py
```

The provided `app.py` also inserts the project root into `sys.path`.

---

### Issue: Browser does not open automatically

Open manually:

```text
http://127.0.0.1:5000
```

---

### Issue: Port already in use

Change the port in `app.py`:

```python
app.run(debug=True, host="127.0.0.1", port=5001)
```

Then open:

```text
http://127.0.0.1:5001
```

---

## 10. Optional Improvement: Save Demo Runs

You can add logging to save each query/result pair to:

```text
results/demo_runs.jsonl
```

This can help you report example outputs later.

---

## 11. Final Recommendation

For the final presentation, use this Flask interface.

It is the best balance of:

- professional appearance,
- real code execution,
- low setup complexity,
- clear connection to your project,
- good live-demo reliability.
