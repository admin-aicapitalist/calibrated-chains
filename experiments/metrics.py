"""Calibration + gate metrics for the binary "is this an invoice?" decision, rendered as markdown.

    uv run python -m experiments.metrics v0_baseline dev
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from experiments.run import run_path

RESULTS = Path(__file__).parent / "results"
GATES = (0.6, 0.7, 0.8, 0.9, 0.95, 0.99)


def load_run(variant: str, sample_name: str, extract=None) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Returns (p_invoice, is_invoice, rows). ``extract(row) -> p`` defaults to is_invoice/true."""
    rows = [json.loads(line) for line in run_path(variant, sample_name).open()]
    extract = extract or default_extract
    return np.array([extract(r) for r in rows]), np.array([r["category"] == "invoice" for r in rows]), rows


def default_extract(row: dict) -> float:
    if "is_invoice" in row["answers"]:
        return prob(row, "is_invoice", "true")
    if "not_invoice" in row["answers"]:
        return prob(row, "not_invoice", "false")
    return prob(row, "doc_type", "invoice")


def prob(row: dict, question: str, option: str) -> float:
    answer = row["answers"][question]
    return answer["probs"][answer["options"].index(option)]


def auroc(p: np.ndarray, y: np.ndarray) -> float:
    ranks = p.argsort().argsort() + 1.0
    for value in np.unique(p):  # average ranks over ties
        ranks[p == value] = ranks[p == value].mean()
    pos, neg = y.sum(), (~y).sum()
    return float((ranks[y].sum() - pos * (pos + 1) / 2) / (pos * neg))


def average_precision(p: np.ndarray, y: np.ndarray) -> float:
    order = np.argsort(-p, kind="stable")
    hits = y[order].cumsum()
    precision = hits / np.arange(1, len(y) + 1)
    return float((precision * y[order]).sum() / y.sum())


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Top-label ECE: confidence = max(p, 1-p) vs accuracy of the thresholded prediction."""
    conf, correct = np.maximum(p, 1 - p), (p >= 0.5) == y
    edges = np.linspace(0.5, 1.0, bins + 1)
    idx = np.clip(np.digitize(conf, edges) - 1, 0, bins - 1)
    return float(sum(abs(conf[idx == b].mean() - correct[idx == b].mean()) * (idx == b).mean()
                     for b in range(bins) if (idx == b).any()))


def summary(p: np.ndarray, y: np.ndarray) -> dict[str, float]:
    pred = p >= 0.5
    tp, fp, fn = (pred & y).sum(), (pred & ~y).sum(), (~pred & y).sum()
    eps = 1e-7
    return {
        "n": len(y), "invoices": int(y.sum()),
        "accuracy": float((pred == y).mean()),
        "precision": float(tp / max(tp + fp, 1)), "recall": float(tp / max(tp + fn, 1)),
        "f1": float(2 * tp / max(2 * tp + fp + fn, 1)),
        "auroc": auroc(p, y), "ap": average_precision(p, y),
        "brier": float(((p - y) ** 2).mean()),
        "nll": float(-(y * np.log(p + eps) + (~y) * np.log(1 - p + eps)).mean()),
        "ece": ece(p, y),
    }


def gate_table(p: np.ndarray, y: np.ndarray) -> list[dict[str, float]]:
    """Monad gate semantics: a decision passes iff max(p, 1-p) >= tau; otherwise the chain blocks."""
    conf, pred = np.maximum(p, 1 - p), p >= 0.5
    out = []
    for tau in GATES:
        passed = conf >= tau
        out.append({
            "tau": tau,
            "coverage": float(passed.mean()),
            "selective_acc": float(((pred == y) & passed).sum() / max(passed.sum(), 1)),
            "silent_errors": int(((pred != y) & passed).sum()),          # wrong AND let through
            "false_invoice": int((pred & ~y & passed).sum()),           # non-invoice passed as invoice
            "missed_invoice": int((~pred & y & passed).sum()),          # invoice confidently rejected
            "invoices_accepted": int((pred & y & passed).sum()),
            "blocked": int((~passed).sum()),
        })
    return out


def reliability(p: np.ndarray, y: np.ndarray, bins: int = 10) -> list[tuple[str, int, float, float]]:
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    return [(f"{edges[b]:.1f}-{edges[b + 1]:.1f}", int((idx == b).sum()),
             float(p[idx == b].mean()) if (idx == b).any() else float("nan"),
             float(y[idx == b].mean()) if (idx == b).any() else float("nan")) for b in range(bins)]


def render(title: str, p: np.ndarray, y: np.ndarray) -> str:
    s = summary(p, y)
    lines = [f"### {title}", "",
             f"n={s['n']} (invoices {s['invoices']}) | acc {s['accuracy']:.3f} | P {s['precision']:.3f} "
             f"R {s['recall']:.3f} F1 {s['f1']:.3f} | AUROC {s['auroc']:.3f} | AP {s['ap']:.3f} | "
             f"Brier {s['brier']:.3f} | NLL {s['nll']:.3f} | ECE {s['ece']:.3f}", "",
             "Reliability (p_invoice bin -> observed invoice rate):", "",
             "| bin | n | mean p | observed |", "|---|---|---|---|"]
    lines += [f"| {b} | {n} | {mp:.3f} | {obs:.3f} |" for b, n, mp, obs in reliability(p, y) if n]
    lines += ["", "Gate (pass iff confidence >= tau):", "",
              "| tau | coverage | selective acc | silent errors | false invoice | missed invoice | invoices accepted | blocked |",
              "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {g['tau']} | {g['coverage']:.3f} | {g['selective_acc']:.3f} | {g['silent_errors']} | "
              f"{g['false_invoice']} | {g['missed_invoice']} | {g['invoices_accepted']} | {g['blocked']} |"
              for g in gate_table(p, y)]
    return "\n".join(lines) + "\n"


def confusions(rows: list[dict], p: np.ndarray, y: np.ndarray, k: int = 8) -> str:
    """Most confident mistakes, plus which non-invoice classes the model calls invoices."""
    pred = p >= 0.5
    cats = np.array([r["category"] for r in rows])
    lines = ["False-positive classes (non-invoice with p>=0.5): " + ", ".join(
        f"{c} {n}" for c, n in zip(*np.unique(cats[pred & ~y], return_counts=True))) or "none"]
    wrong = np.where(pred != y)[0]
    worst = wrong[np.argsort(-np.abs(p[wrong] - 0.5))][:k]
    lines += [f"- {rows[i]['doc_id']} ({rows[i]['category']}): p_invoice={p[i]:.3f}" for i in worst]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    variant, sample_name = sys.argv[1:3]
    p, y, rows = load_run(variant, sample_name)
    print(render(f"{variant} on {sample_name}", p, y))
    print(confusions(rows, p, y))
