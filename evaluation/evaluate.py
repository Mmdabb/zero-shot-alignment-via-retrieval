"""End-to-end evaluation of the Zero-Shot Alignment via Retrieval system.

Metrics:
  1. Retrieval Accuracy
       top-1 / top-2 accuracy + per-style precision/recall + confusion matrix
  2. Style Adherence (Schema)
       avoid-word rate (lower = better) and prefer-word rate (higher = better)
       compared against (a) the original text and (b) the schema-rewritten text
  3. Style Adherence (Embedding)
       cos-sim(rewrite, style_description) - cos-sim(original, style_description)
       positive = the rewrite is closer to the target style
  4. Latency
       per-stage wall-clock time over the offline path (retrieval + schema rewrite)
       optionally a small github-models sample for comparison

Baselines:
  - Random retrieval (uniform over the 4 styles)
  - "No alignment" = the original text scored against its expected style
"""

from __future__ import annotations

import json
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT / ".env")

from alignment.embeddings import EmbeddingModule
from alignment.retrieval import RetrievalModule
from alignment.style_library import StyleLibrary
from alignment.style_schema import STYLE_SCHEMAS, get_style_schema
from alignment.fallback_generator import schema_rewrite

DATA_PATH = ROOT / "data" / "eval_dataset.jsonl"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)
OUT_PATH = RESULTS_DIR / "metrics.json"

STYLES = ["formal", "casual", "technical", "friendly"]
SEED = 579
random.seed(SEED)


# ---------- helpers ----------

def load_dataset() -> list[dict]:
    examples = []
    with DATA_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def word_hit_rate(text: str, words: list[str]) -> float:
    """Fraction of words/phrases from `words` that appear in `text` (case-insensitive)."""
    if not words:
        return 0.0
    text_low = text.lower()
    hits = sum(1 for w in words if w.lower() in text_low)
    return hits / len(words)


def avoid_prefer_rates(text: str, style: str) -> tuple[float, float]:
    schema = get_style_schema(style)
    avoid = schema["wording"]["avoid"]
    prefer = schema["wording"]["prefer"]
    return word_hit_rate(text, avoid), word_hit_rate(text, prefer)


def percent(x: float, n: int = 2) -> float:
    return round(100.0 * x, n)


# ---------- metric computations ----------

def evaluate_retrieval(examples, retrieval, lib):
    print("[1] Retrieval accuracy ...")
    top1_correct = 0
    top2_correct = 0
    confusion = defaultdict(lambda: Counter())  # confusion[expected][predicted]
    per_style_total = Counter()
    per_style_top1 = Counter()
    latencies = []

    for ex in examples:
        text = ex["text"]
        expected = ex["expected_style"]
        per_style_total[expected] += 1

        t0 = time.perf_counter()
        top_k = retrieval.retrieve_top_k(text, lib.styles, k=2)
        latencies.append(time.perf_counter() - t0)

        predicted = top_k[0][0]
        confusion[expected][predicted] += 1
        if predicted == expected:
            top1_correct += 1
            per_style_top1[expected] += 1
        if any(name == expected for name, _ in top_k):
            top2_correct += 1

    n = len(examples)

    # per-style precision / recall from confusion matrix
    per_style_metrics = {}
    for s in STYLES:
        tp = confusion[s][s]
        fp = sum(confusion[other][s] for other in STYLES if other != s)
        fn = sum(confusion[s][other] for other in STYLES if other != s)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        per_style_metrics[s] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "support": per_style_total[s],
        }

    return {
        "n": n,
        "top1_accuracy": round(top1_correct / n, 4),
        "top2_accuracy": round(top2_correct / n, 4),
        "per_style": per_style_metrics,
        "confusion_matrix": {
            row: {col: confusion[row][col] for col in STYLES} for row in STYLES
        },
        "retrieval_latency_ms": {
            "mean": round(statistics.mean(latencies) * 1000, 3),
            "p50": round(statistics.median(latencies) * 1000, 3),
            "p95": round(sorted(latencies)[int(0.95 * len(latencies)) - 1] * 1000, 3),
        },
    }


def evaluate_random_baseline(examples, n_runs: int = 50):
    print("[1b] Random retrieval baseline ...")
    accuracies = []
    rng = random.Random(SEED)
    for _ in range(n_runs):
        correct = sum(1 for ex in examples
                      if rng.choice(STYLES) == ex["expected_style"])
        accuracies.append(correct / len(examples))
    return {
        "n_runs": n_runs,
        "mean_accuracy": round(statistics.mean(accuracies), 4),
        "stdev_accuracy": round(statistics.stdev(accuracies), 4),
    }


# Keyword lists derived from STYLE_SCHEMAS (avoid/prefer wording, opening cues)
# plus generic style indicators that a non-ML programmer would think of first.
KEYWORD_RULES = {
    "formal":    ["regarding", "would like", "therefore", "recommend",
                  "hereby", "furthermore", "shall", "request", "kindly", "professional"],
    "casual":    ["hey", "yeah", "wanna", "kinda", "lol", "stuff", "thing",
                  "basically", "pretty much", "gonna"],
    "technical": ["algorithm", "function", "parameter", "module", "API", "implement",
                  "code", "error", "variable", "method", "process", "system"],
    "friendly":  ["hi", "hope", "happy", "great", "love", "feel", "thanks",
                  "wonderful", "appreciate", "kind", "warm", "support"],
}


def keyword_predict(text: str) -> str:
    """Predict style by counting keyword hits per style; ties → 'formal' default."""
    text_low = text.lower()
    scores = {style: sum(1 for kw in kws if kw.lower() in text_low)
              for style, kws in KEYWORD_RULES.items()}
    best_style = max(scores, key=lambda s: (scores[s], -STYLES.index(s)))
    if scores[best_style] == 0:
        return "formal"  # deterministic tie-break when no keyword matches
    return best_style


def evaluate_keyword_baseline(examples):
    print("[1c] Keyword-rule baseline ...")
    correct = 0
    confusion = defaultdict(lambda: Counter())
    per_style_total = Counter()
    per_style_correct = Counter()

    for ex in examples:
        expected = ex["expected_style"]
        per_style_total[expected] += 1
        predicted = keyword_predict(ex["text"])
        confusion[expected][predicted] += 1
        if predicted == expected:
            correct += 1
            per_style_correct[expected] += 1

    per_style = {}
    for s in STYLES:
        tp = confusion[s][s]
        fp = sum(confusion[other][s] for other in STYLES if other != s)
        fn = sum(confusion[s][other] for other in STYLES if other != s)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        per_style[s] = {"precision": round(prec, 4), "recall": round(rec, 4),
                        "support": per_style_total[s]}

    return {
        "accuracy": round(correct / len(examples), 4),
        "per_style": per_style,
        "confusion_matrix": {row: {col: confusion[row][col] for col in STYLES}
                             for row in STYLES},
        "keyword_lists_size": {s: len(kws) for s, kws in KEYWORD_RULES.items()},
    }


def evaluate_style_adherence_schema(examples, embedding):
    """Schema-based + embedding-based adherence on the same pass.

    For each example we compute:
      - avoid/prefer rates on the ORIGINAL text (no-alignment baseline)
      - avoid/prefer rates on the SCHEMA-REWRITTEN text (alignment effect)
      - cos-sim(text, style_description) before vs after
    We expect: avoid ↓, prefer ↑, embedding sim ↑ after alignment.
    """
    print("[2] Style adherence (schema + embedding) ...")
    schema = STYLE_SCHEMAS
    style_desc_emb = {s: embedding.embed_text(STYLE_SCHEMAS[s]["rewrite_goal"]) for s in STYLES}

    by_style = defaultdict(lambda: {
        "avoid_before": [], "avoid_after": [],
        "prefer_before": [], "prefer_after": [],
        "sim_before": [], "sim_after": [],
        "rewrite_latency_ms": [],
    })

    for ex in examples:
        style = ex["expected_style"]
        text = ex["text"]

        avoid_b, prefer_b = avoid_prefer_rates(text, style)

        t0 = time.perf_counter()
        rewritten = schema_rewrite(text, style, get_style_schema(style))
        rewrite_latency_ms = (time.perf_counter() - t0) * 1000

        avoid_a, prefer_a = avoid_prefer_rates(rewritten, style)

        emb_text = embedding.embed_text(text)
        emb_rewrite = embedding.embed_text(rewritten)
        sim_b = embedding.cosine_similarity(emb_text, style_desc_emb[style])
        sim_a = embedding.cosine_similarity(emb_rewrite, style_desc_emb[style])

        by_style[style]["avoid_before"].append(avoid_b)
        by_style[style]["avoid_after"].append(avoid_a)
        by_style[style]["prefer_before"].append(prefer_b)
        by_style[style]["prefer_after"].append(prefer_a)
        by_style[style]["sim_before"].append(sim_b)
        by_style[style]["sim_after"].append(sim_a)
        by_style[style]["rewrite_latency_ms"].append(rewrite_latency_ms)

    summary = {}
    overall_avoid_b, overall_avoid_a = [], []
    overall_prefer_b, overall_prefer_a = [], []
    overall_sim_b, overall_sim_a = [], []
    overall_latency = []

    for style in STYLES:
        d = by_style[style]
        summary[style] = {
            "n": len(d["avoid_before"]),
            "avoid_rate_before": round(statistics.mean(d["avoid_before"]), 4),
            "avoid_rate_after": round(statistics.mean(d["avoid_after"]), 4),
            "prefer_rate_before": round(statistics.mean(d["prefer_before"]), 4),
            "prefer_rate_after": round(statistics.mean(d["prefer_after"]), 4),
            "embedding_sim_before": round(statistics.mean(d["sim_before"]), 4),
            "embedding_sim_after": round(statistics.mean(d["sim_after"]), 4),
            "rewrite_latency_ms_mean": round(statistics.mean(d["rewrite_latency_ms"]), 3),
        }
        overall_avoid_b += d["avoid_before"]; overall_avoid_a += d["avoid_after"]
        overall_prefer_b += d["prefer_before"]; overall_prefer_a += d["prefer_after"]
        overall_sim_b += d["sim_before"]; overall_sim_a += d["sim_after"]
        overall_latency += d["rewrite_latency_ms"]

    return {
        "per_style": summary,
        "overall": {
            "avoid_rate_before": round(statistics.mean(overall_avoid_b), 4),
            "avoid_rate_after": round(statistics.mean(overall_avoid_a), 4),
            "prefer_rate_before": round(statistics.mean(overall_prefer_b), 4),
            "prefer_rate_after": round(statistics.mean(overall_prefer_a), 4),
            "embedding_sim_before": round(statistics.mean(overall_sim_b), 4),
            "embedding_sim_after": round(statistics.mean(overall_sim_a), 4),
            "rewrite_latency_ms_mean": round(statistics.mean(overall_latency), 3),
        },
    }


def evaluate_github_latency_sample(examples, n: int = 6):
    """Optional small-sample latency comparison against GitHub Models.
    Skips silently if the provider is not configured / unavailable."""
    print(f"[3] GitHub Models latency sample (n={n}) ...")
    try:
        from alignment.providers.github_provider import GitHubModelsProvider
        provider = GitHubModelsProvider()
        if not provider.is_available():
            return {"skipped": "provider unavailable"}
    except Exception as e:
        return {"skipped": f"import/init error: {type(e).__name__}: {e}"}

    sample = random.sample(examples, min(n, len(examples)))
    latencies = []
    failures = 0
    for ex in sample:
        try:
            t0 = time.perf_counter()
            res = provider.generate_aligned_response(
                user_query="",
                base_response=ex["text"],
                style_name=ex["expected_style"],
                style_description=STYLE_SCHEMAS[ex["expected_style"]]["rewrite_goal"],
                style_schema=STYLE_SCHEMAS[ex["expected_style"]],
            )
            latencies.append((time.perf_counter() - t0) * 1000)
            if not res.success:
                failures += 1
        except Exception:
            failures += 1
    if not latencies:
        return {"skipped": "all calls failed", "failures": failures}
    return {
        "n": len(latencies),
        "failures": failures,
        "latency_ms_mean": round(statistics.mean(latencies), 1),
        "latency_ms_p50": round(statistics.median(latencies), 1),
    }


# ---------- driver ----------

def main() -> int:
    print(f"Loading {DATA_PATH} ...")
    examples = load_dataset()
    print(f"  loaded {len(examples)} examples")

    print("Loading retrieval components ...")
    lib = StyleLibrary()
    emb = EmbeddingModule()
    retrieval = RetrievalModule(emb)
    retrieval.index_styles(lib.styles)

    metrics = {
        "dataset": {
            "path": str(DATA_PATH),
            "size": len(examples),
            "per_style_counts": dict(Counter(ex["expected_style"] for ex in examples)),
        },
        "retrieval": evaluate_retrieval(examples, retrieval, lib),
        "random_baseline": evaluate_random_baseline(examples),
        "keyword_baseline": evaluate_keyword_baseline(examples),
        "style_adherence": evaluate_style_adherence_schema(examples, emb),
        "github_latency_sample": evaluate_github_latency_sample(examples, n=6),
    }

    with OUT_PATH.open("w") as f:
        json.dump(metrics, f, indent=2)

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Retrieval top-1 acc : {percent(metrics['retrieval']['top1_accuracy'])}%")
    print(f"Retrieval top-2 acc : {percent(metrics['retrieval']['top2_accuracy'])}%")
    print(f"Random baseline acc : {percent(metrics['random_baseline']['mean_accuracy'])}% "
          f"(stdev {percent(metrics['random_baseline']['stdev_accuracy'])}%)")
    print(f"Keyword baseline acc: {percent(metrics['keyword_baseline']['accuracy'])}%")
    print(f"Schema adherence    : avoid {percent(metrics['style_adherence']['overall']['avoid_rate_before'])}% "
          f"-> {percent(metrics['style_adherence']['overall']['avoid_rate_after'])}%, "
          f"prefer {percent(metrics['style_adherence']['overall']['prefer_rate_before'])}% "
          f"-> {percent(metrics['style_adherence']['overall']['prefer_rate_after'])}%")
    print(f"Embedding sim       : {metrics['style_adherence']['overall']['embedding_sim_before']:.4f} "
          f"-> {metrics['style_adherence']['overall']['embedding_sim_after']:.4f}")
    print(f"Retrieval latency   : mean {metrics['retrieval']['retrieval_latency_ms']['mean']} ms")
    print(f"Schema rewrite lat. : mean {metrics['style_adherence']['overall']['rewrite_latency_ms_mean']} ms")
    gh = metrics["github_latency_sample"]
    if "latency_ms_mean" in gh:
        print(f"GitHub Models lat.  : mean {gh['latency_ms_mean']} ms (n={gh['n']}, failures={gh['failures']})")
    else:
        print(f"GitHub Models lat.  : {gh.get('skipped','n/a')}")

    print(f"\nFull metrics -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
