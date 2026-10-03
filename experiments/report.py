"""Write experiments/results/<variant>__<sample>.md: raw metrics, recalibrated metrics, picked gate.

    uv run python -m experiments.report v0_baseline dev
"""

from __future__ import annotations

import sys

import numpy as np

from experiments.calibrate import cross_val_logreg, cross_val_platt, logit, pick_tau
from experiments.metrics import RESULTS, confusions, load_run, prob, render, summary

TARGET_SILENT = 0.01  # at most 1% of passed decisions may be wrong


def evidence_features(rows: list[dict]) -> tuple[np.ndarray, list[str]]:
    """Logit of every yes/no answer plus logit P(doc_type=invoice), for stacking."""
    names = [q for q, a in rows[0]["answers"].items() if a["options"] == ["true", "false"]]
    cols = [logit(np.array([prob(r, q, "true") for r in rows])) for q in names]
    if "doc_type" in rows[0]["answers"]:
        names.append("doc_type=invoice")
        cols.append(logit(np.array([prob(r, "doc_type", "invoice") for r in rows])))
    return np.stack(cols, 1), names


def gate_line(name: str, p: np.ndarray, y: np.ndarray) -> str:
    tau = pick_tau(p, y, TARGET_SILENT)
    conf, wrong = np.maximum(p, 1 - p), (p >= 0.5) != y
    passed = conf >= tau
    s = summary(p, y)
    return (f"| {name} | {s['accuracy']:.3f} | {s['auroc']:.3f} | {s['brier']:.3f} | {s['ece']:.3f} | {tau:.3f} | "
            f"{passed.mean():.3f} | {int((wrong & passed).sum())} | {int((passed & (p >= 0.5) & y).sum())}/{int(y.sum())} |")


def main(variant: str, sample_name: str) -> str:
    p, y, rows = load_run(variant, sample_name)
    out = [f"# {variant} on {sample_name}", "", render("Raw Clef probabilities", p, y), confusions(rows, p, y)]

    strategies = {"raw": p, "platt (5-fold CV)": cross_val_platt(p, y)}
    if "doc_type" in rows[0]["answers"] and "is_invoice" in rows[0]["answers"]:
        p_type = np.array([prob(r, "doc_type", "invoice") for r in rows])
        strategies["doc_type=invoice only"] = p_type
        strategies["mean(is_invoice, doc_type)"] = (p + p_type) / 2
        # Symbolic AND-gate: both independent framings must agree, else the lower one decides.
        strategies["agree: min if both yes, max if both no"] = np.where((p >= 0.5) & (p_type >= 0.5),
                                                                        np.minimum(p, p_type),
                                                                        np.where((p < 0.5) & (p_type < 0.5),
                                                                                 np.maximum(p, p_type), 0.5))
        x, names = evidence_features(rows)
        strategies[f"stacked logreg over {len(names)} answers (5-fold CV)"] = cross_val_logreg(x, y)
    out += ["## Strategies, gate tuned for <= 1% silent errors", "",
            "Each row's tau is the lowest that keeps silent errors <= 1% of passed decisions *on this same "
            "sample*; it's an optimistic in-sample pick, and only the test run checks it.", "",
            "| strategy | acc | AUROC | Brier | ECE | tau | coverage | silent errors | invoices auto-accepted |",
            "|---|---|---|---|---|---|---|---|---|"]
    out += [gate_line(name, q, y) for name, q in strategies.items()]
    text = "\n".join(out) + "\n"
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{variant}__{sample_name}.md").write_text(text)
    return text


if __name__ == "__main__":
    print(main(*sys.argv[1:3]))
