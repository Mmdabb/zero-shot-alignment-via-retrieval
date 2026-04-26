"""Generate result plots from results/metrics.json.

Outputs:
  results/confusion_matrix.png
  results/style_adherence_comparison.png
  results/latency_bar.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
METRICS_PATH = RESULTS_DIR / "metrics.json"

STYLES = ["formal", "casual", "technical", "friendly"]


def load_metrics() -> dict:
    with METRICS_PATH.open() as f:
        return json.load(f)


def plot_confusion(metrics: dict) -> Path:
    cm = metrics["retrieval"]["confusion_matrix"]
    matrix = np.array([[cm[r][c] for c in STYLES] for r in STYLES])

    # row-normalize so each row sums to 1 (recall view)
    row_sums = matrix.sum(axis=1, keepdims=True)
    norm = np.divide(matrix, row_sums, where=row_sums != 0)

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(STYLES)), STYLES)
    ax.set_yticks(range(len(STYLES)), STYLES)
    ax.set_xlabel("Predicted style")
    ax.set_ylabel("Expected style (ground truth)")
    ax.set_title(
        f"Retrieval Confusion Matrix (row-normalized)\n"
        f"Embedding top-1 = {metrics['retrieval']['top1_accuracy']:.1%}, "
        f"top-2 = {metrics['retrieval']['top2_accuracy']:.1%}  |  "
        f"keyword baseline = {metrics['keyword_baseline']['accuracy']:.1%}, "
        f"random = {metrics['random_baseline']['mean_accuracy']:.1%}"
    )
    for i in range(len(STYLES)):
        for j in range(len(STYLES)):
            ax.text(j, i, f"{matrix[i, j]}\n({norm[i, j]:.0%})",
                    ha="center", va="center",
                    color="white" if norm[i, j] > 0.5 else "black",
                    fontsize=9)
    fig.colorbar(im, ax=ax, label="Recall (row-normalized)")
    fig.tight_layout()
    out = RESULTS_DIR / "confusion_matrix.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_adherence(metrics: dict) -> Path:
    per = metrics["style_adherence"]["per_style"]
    overall = metrics["style_adherence"]["overall"]

    labels = STYLES + ["overall"]
    avoid_b = [per[s]["avoid_rate_before"] * 100 for s in STYLES] + [overall["avoid_rate_before"] * 100]
    avoid_a = [per[s]["avoid_rate_after"] * 100 for s in STYLES] + [overall["avoid_rate_after"] * 100]
    prefer_b = [per[s]["prefer_rate_before"] * 100 for s in STYLES] + [overall["prefer_rate_before"] * 100]
    prefer_a = [per[s]["prefer_rate_after"] * 100 for s in STYLES] + [overall["prefer_rate_after"] * 100]
    sim_b = [per[s]["embedding_sim_before"] for s in STYLES] + [overall["embedding_sim_before"]]
    sim_a = [per[s]["embedding_sim_after"] for s in STYLES] + [overall["embedding_sim_after"]]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    x = np.arange(len(labels))
    w = 0.38

    axes[0].bar(x - w / 2, avoid_b, w, label="before", color="#cf6e6e")
    axes[0].bar(x + w / 2, avoid_a, w, label="after",  color="#5a9c5a")
    axes[0].set_xticks(x, labels, rotation=20)
    axes[0].set_ylabel("avoid-word hit rate (%)")
    axes[0].set_title("Avoid words (lower is better)")
    axes[0].legend()

    axes[1].bar(x - w / 2, prefer_b, w, label="before", color="#cf6e6e")
    axes[1].bar(x + w / 2, prefer_a, w, label="after",  color="#5a9c5a")
    axes[1].set_xticks(x, labels, rotation=20)
    axes[1].set_ylabel("prefer-word hit rate (%)")
    axes[1].set_title("Prefer words (higher is better)")
    axes[1].legend()

    axes[2].bar(x - w / 2, sim_b, w, label="before", color="#cf6e6e")
    axes[2].bar(x + w / 2, sim_a, w, label="after",  color="#5a9c5a")
    axes[2].set_xticks(x, labels, rotation=20)
    axes[2].set_ylabel("cos-sim(text, style description)")
    axes[2].set_title("Embedding similarity (higher is better)")
    axes[2].legend()

    fig.suptitle("Style Adherence: Original Text vs Schema-Rewritten", y=1.02)
    fig.tight_layout()
    out = RESULTS_DIR / "style_adherence_comparison.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_latency(metrics: dict) -> Path:
    retrieval_lat = metrics["retrieval"]["retrieval_latency_ms"]["mean"]
    schema_lat = metrics["style_adherence"]["overall"]["rewrite_latency_ms_mean"]
    gh = metrics.get("github_latency_sample", {})
    has_gh = "latency_ms_mean" in gh

    labels = ["Retrieval\n(MiniLM)", "Schema\nrewrite", "GitHub Models\n(gpt-4o-mini)" if has_gh else None]
    values = [retrieval_lat, schema_lat, gh.get("latency_ms_mean", 0) if has_gh else None]
    colors = ["#4a90e2", "#5a9c5a", "#e29a4a"]

    labels = [l for l in labels if l is not None]
    values = [v for v in values if v is not None]
    colors = colors[: len(labels)]

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    bars = ax.bar(labels, values, color=colors)
    ax.set_yscale("log")
    ax.set_ylabel("Mean latency (ms, log scale)")
    ax.set_title("Per-stage Latency Comparison")
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v * 1.15,
                f"{v:.3g} ms", ha="center", va="bottom", fontsize=10)
    ax.grid(axis="y", which="both", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = RESULTS_DIR / "latency_bar.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_baseline_comparison(metrics: dict) -> Path:
    labels = ["Random\n(uniform)", "Keyword\nrules", "Embedding\ntop-1", "Embedding\ntop-2"]
    values = [
        metrics["random_baseline"]["mean_accuracy"] * 100,
        metrics["keyword_baseline"]["accuracy"] * 100,
        metrics["retrieval"]["top1_accuracy"] * 100,
        metrics["retrieval"]["top2_accuracy"] * 100,
    ]
    colors = ["#b0b0b0", "#cf6e6e", "#4a90e2", "#1f4e8c"]

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    bars = ax.bar(labels, values, color=colors)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Accuracy on 160-example eval set (%)")
    ax.set_title("Retrieval Method Comparison")
    ax.axhline(25, color="gray", linestyle=":", alpha=0.6)
    ax.text(3.5, 26, "chance level (25%)", ha="right", va="bottom",
            color="gray", fontsize=9)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5,
                f"{v:.1f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")
    fig.tight_layout()
    out = RESULTS_DIR / "baseline_comparison.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def main() -> int:
    metrics = load_metrics()
    paths = [
        plot_confusion(metrics),
        plot_baseline_comparison(metrics),
        plot_adherence(metrics),
        plot_latency(metrics),
    ]
    print("Wrote plots:")
    for p in paths:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
