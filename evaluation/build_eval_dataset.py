"""Build a 4-style evaluation dataset by merging three public sources.

Output: data/eval_dataset.jsonl  (one JSON per line: {"text": str, "expected_style": str, "source": str})

Coverage:
  formal    -> Pavlick & Tetreault formality scores (avg_score >= 1.0)
  casual    -> Pavlick & Tetreault formality scores (avg_score <= -1.0)
  friendly  -> EmpatheticDialogues (positive empathy emotions)
  technical -> ConvoKit Stanford Politeness Stack Exchange half
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_PATH = DATA_DIR / "eval_dataset.jsonl"

PER_STYLE = 40
SEED = 579  # CSE 579
random.seed(SEED)

FRIENDLY_EMOTIONS = {
    "caring", "grateful", "joyful", "hopeful", "trusting",
    "sentimental", "proud", "content", "faithful", "confident",
}


def _clean(text: str) -> str:
    return " ".join(text.strip().split())


def _is_reasonable(text: str, lo: int = 30, hi: int = 400) -> bool:
    return lo <= len(text) <= hi


def collect_formal_casual() -> list[dict]:
    from datasets import load_dataset
    print("[formal/casual] loading osyvokon/pavlick-formality-scores ...")
    ds = load_dataset("osyvokon/pavlick-formality-scores", split="train")

    formal_pool = []
    casual_pool = []
    for row in ds:
        text = _clean(row["sentence"])
        if not _is_reasonable(text):
            continue
        score = float(row["avg_score"])
        if score >= 1.0:
            formal_pool.append({"text": text, "expected_style": "formal",
                                "source": f"pavlick:{row.get('domain','?')}"})
        elif score <= -1.0:
            casual_pool.append({"text": text, "expected_style": "casual",
                                "source": f"pavlick:{row.get('domain','?')}"})

    print(f"  formal pool={len(formal_pool)}  casual pool={len(casual_pool)}")
    random.shuffle(formal_pool)
    random.shuffle(casual_pool)
    return formal_pool[:PER_STYLE] + casual_pool[:PER_STYLE]


def collect_friendly() -> list[dict]:
    from datasets import load_dataset
    print("[friendly] loading Estwld/empathetic_dialogues_llm ...")
    ds = load_dataset("Estwld/empathetic_dialogues_llm", split="train")

    pool = []
    seen = set()
    for row in ds:
        emotion = (row.get("emotion") or "").lower()
        if emotion not in FRIENDLY_EMOTIONS:
            continue
        # Use the first user turn as a representative friendly utterance.
        for turn in row.get("conversations", []):
            if turn.get("role") != "user":
                continue
            text = _clean(turn.get("content", ""))
            if not _is_reasonable(text):
                continue
            if text in seen:
                continue
            seen.add(text)
            pool.append({"text": text, "expected_style": "friendly",
                         "source": f"empathetic:{emotion}"})
            break  # one per conversation

    print(f"  friendly pool={len(pool)}")
    random.shuffle(pool)
    return pool[:PER_STYLE]


def collect_technical() -> list[dict]:
    """Use ConvoKit Stanford Politeness SE corpus — every utterance is a
    Stack Exchange request, so the domain is technical."""
    from convokit import Corpus, download
    print("[technical] downloading stack-exchange-politeness-corpus via convokit ...")
    corpus = Corpus(filename=download("stack-exchange-politeness-corpus"))

    pool = []
    seen = set()
    for utt in corpus.iter_utterances():
        text = _clean(utt.text)
        if not _is_reasonable(text):
            continue
        if text in seen:
            continue
        seen.add(text)
        pool.append({"text": text, "expected_style": "technical",
                     "source": "stanford-politeness-se"})

    print(f"  technical pool={len(pool)}")
    random.shuffle(pool)
    return pool[:PER_STYLE]


def main() -> int:
    examples = []
    examples += collect_formal_casual()
    examples += collect_friendly()
    examples += collect_technical()

    random.shuffle(examples)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    counts = {}
    for ex in examples:
        counts[ex["expected_style"]] = counts.get(ex["expected_style"], 0) + 1

    print(f"\nWrote {len(examples)} examples to {OUT_PATH}")
    for k in ["formal", "casual", "friendly", "technical"]:
        print(f"  {k:10s} {counts.get(k, 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
