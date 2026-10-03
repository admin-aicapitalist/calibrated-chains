"""One row per finished variant on a sample: the invoice-handling metrics the approval chain cares about.

    uv run python -m experiments.compare bal120
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from experiments.calibrate import cross_val_platt, pick_tau
from experiments.metrics import RESULTS, load_run, summary
from experiments.run import RUNS
from experiments.variants import VARIANTS

AUDIT = Path(__file__).parent / "label_noise.md"


def corrections() -> dict[str, bool]:
    """doc_id -> audited is_invoice, parsed from the label_noise.md table."""
    out = {}
    for line in AUDIT.read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3 and "/" in cells[0] and not cells[0].startswith("-"):
            out[cells[0]] = cells[2] == "invoice"
    return out


def gate_at(p: np.ndarray, y: np.ndarray, tau: float) -> tuple[int, int, int]:
    passed = np.maximum(p, 1 - p) >= tau
    pred = p >= 0.5
    return int((pred & y & passed).sum()), int((pred & ~y & passed).sum()), int((~pred & y & passed).sum())


def row(name: str, p: np.ndarray, y: np.ndarray) -> str:
    s = summary(p, y)
    acc9, false9, miss9 = gate_at(p, y, 0.9)
    tau = pick_tau(p, y, 0.01)
    safe_acc, safe_false, _ = gate_at(p, y, tau)
    return (f"| {name} | {s['recall']:.3f} | {s['precision']:.3f} | {s['auroc']:.3f} | {s['ece']:.3f} | "
            f"{acc9} / {false9} / {miss9} | {tau:.3f} | {safe_acc} / {safe_false} |")


def main(sample_name: str, corrected: bool = False) -> str:
    n_expected = None
    lines = [f"## Variants on {sample_name}" + (" (audited labels, see label_noise.md)" if corrected else ""), "",
             "- **@0.9**: at τ=0.9, invoices accepted / false invoices passed / invoices confidently rejected.",
             "- **safe τ**: lowest τ with ≤1% silent errors on this sample (in-sample pick), and invoices "
             "auto-accepted / false invoices at that τ.", "",
             "| variant | recall | precision | AUROC | ECE | @0.9 acc/false/missed | safe τ | safe acc/false |",
             "|---|---|---|---|---|---|---|---|"]
    for variant in VARIANTS:
        path = RUNS / f"{variant}__{sample_name}.jsonl"
        if not path.exists():
            continue
        p, y, rows = load_run(variant, sample_name)
        if corrected:
            fixes = corrections()
            y = np.array([fixes.get(r["doc_id"], label) for r, label in zip(rows, y)])
        n_expected = n_expected or len(rows)
        if len(rows) < n_expected:
            lines.append(f"| {variant} | (running: {len(rows)}/{n_expected}) |||||||")
            continue
        lines.append(row(variant, p, y))
        lines.append(row(f"{variant} + platt(CV)", cross_val_platt(p, y), y))
    text = "\n".join(lines) + "\n"
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"compare__{sample_name}{'__audited' if corrected else ''}.md").write_text(text)
    return text


if __name__ == "__main__":
    print(main(sys.argv[1]))
    print(main(sys.argv[1], corrected=True))
