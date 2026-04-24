"""
Flask web interface for the Zero-Shot Alignment via Retrieval project.

Run from the project root:

    python web_demo/app.py

Then open:

    http://127.0.0.1:5000
"""

from pathlib import Path
import sys
import logging
from flask import Flask, render_template, request, jsonify

# ---------------------------------------------------------------------
# Make sure the project root is available so we can import alignment/.
# This assumes the structure:
#
# KRR_project/
# ├── alignment/
# └── web_demo/
#     └── app.py
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from alignment.logging_config import setup_logging
    from alignment import ZeroShotAlignmentSystem
except Exception as exc:
    ZeroShotAlignmentSystem = None
    IMPORT_ERROR = str(exc)
else:
    IMPORT_ERROR = None

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Initialize once so the demo is fast.
if IMPORT_ERROR is None:
    setup_logging()
system = ZeroShotAlignmentSystem() if ZeroShotAlignmentSystem is not None else None


@app.route("/")
def index():
    """Serve the main demo page."""
    return render_template("index.html", import_error=IMPORT_ERROR)


@app.route("/health", methods=["GET"])
def health():
    """Simple health-check endpoint."""
    return jsonify({
        "status": "ok" if system is not None else "error",
        "import_error": IMPORT_ERROR,
    })


@app.route("/align", methods=["POST"])
def align():
    """
    Run the actual Python alignment system.

    Expected JSON:
    {
      "prompt": "...",
      "response": "optional"
    }
    """
    if system is None:
        logger.error("Flask /align request failed before initialization: %s", IMPORT_ERROR)
        return jsonify({
            "error": "Could not import or initialize ZeroShotAlignmentSystem.",
            "details": IMPORT_ERROR,
        }), 500

    data = request.get_json(force=True) or {}
    prompt = (data.get("prompt") or "").strip()
    response = (data.get("response") or "").strip()
    logger.info(
        "Flask /align request start prompt_length=%s override_provided=%s",
        len(prompt),
        bool(response),
    )

    if not prompt:
        logger.warning("Flask /align rejected empty prompt")
        return jsonify({"error": "Prompt is required."}), 400

    try:
        result = system.align_response(prompt=prompt, response=response or None)
        logger.info(
            "Flask /align request end base_provider=%s alignment_provider=%s",
            result.get("base_provider"),
            result.get("alignment_provider"),
        )
        return jsonify(result)
    except Exception as exc:
        logger.exception("Unhandled exception in Flask /align")
        return jsonify({
            "error": "Alignment failed.",
            "details": str(exc),
        }), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
