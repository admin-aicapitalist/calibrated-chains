"""Compile the full invoice-approval chain on Claude-labeled invoices, verify it on held-out documents.

    uv run python -m experiments.compile_chain 0.10 0.20

Chain: is_invoice -> invoice_type (standard|recurring continue) -> amount_consistent -> under_5000 -> payable
-> decide. Approval is symbolic (the AND of every passed gate): Clef's single policy question failed (C5), so
the policy was lowered into atomic conditions, each a calibrated neural step.
Labels: steps 2-4 and the invoice check come from Claude labels (labels/batch_*.jsonl, silver labels made
from scan + OCR); documents RVL-CDIP labels as non-invoices are taken as non-invoices that must not be
approved. Clef answers come from the `c_text` run (all chain questions in one forward pass).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from compiler import AnswerCache, Candidate, Compiler, Example, Map, NeuralStep
from experiments.compare import corrections
from experiments.data import load
from experiments.metrics import RESULTS
from experiments.run import run_path
from experiments.variants import VARIANTS

LABELS = Path(__file__).parent.parent / "labels"
VARIANT = "c_text"
ATOMS = "c_atoms"
SOURCE = {"is_invoice": VARIANT, "invoice_type": VARIANT, "amount_consistent": VARIANT,
          "under_5000": ATOMS, "payable": ATOMS}
STEPS = list(SOURCE)
TEXTS: dict[str, str] = {}


def claude_labels() -> dict[str, dict]:
    out = {}
    for path in sorted(LABELS.glob("batch_*.jsonl")):
        for line in path.open():
            if line.strip():
                row = json.loads(line)
                out[row["doc_id"]] = row
    return out


def builder(variant: str):
    return lambda doc_id: VARIANTS[variant](TEXTS[doc_id])


def candidate(step: str) -> Candidate:
    return Candidate(SOURCE[step], build=builder(SOURCE[step]))


def spec(stop_budget: float) -> list:
    def step(name: str, kind: str = "noul", **kw) -> NeuralStep:
        return NeuralStep(name, kind, [candidate(name)], budget_on="continue", stop_budget=stop_budget, **kw)
    return [
        step("is_invoice"),
        step("invoice_type", "choice", allowed=frozenset({"standard", "recurring"})),
        step("amount_consistent"),
        step("under_5000"),
        step("payable"),
        Map("decide", lambda ctx: "APPROVE"),
    ]


def examples(sample_name: str, cache: AnswerCache, labels: dict[str, dict]) -> list[Example]:
    """Labeled examples for one sample; seeds the cache with the run's per-question probabilities."""
    fixes = corrections()
    atoms = {}
    for name in ("chain_atoms",):
        if run_path(ATOMS, name).exists():
            atoms |= {r["doc_id"]: r for r in map(json.loads, run_path(ATOMS, name).open())}
    out = []
    for row in map(json.loads, run_path(VARIANT, sample_name).open()):
        doc_id = row["doc_id"]
        for step in STEPS:
            source = row if SOURCE[step] == VARIANT else atoms.get(doc_id)
            if source is None:  # no atomic-condition answer for this doc: uninformative, so the gate blocks
                probs = {"true": 0.5, "false": 0.5}
            else:
                answer = source["answers"][step]
                probs = dict(zip(answer["options"], answer["probs"]))
            cache.data[AnswerCache.key(step, SOURCE[step], doc_id, builder(SOURCE[step])(doc_id))] = probs
        claude = labels.get(doc_id)
        if claude:  # labeled by Claude: every step that applies
            approve = bool(claude["approve"])
            ex = {"is_invoice": bool(claude["is_invoice"]), "approve": approve, "payable": approve,
                  "amount_consistent": bool(claude["amount_consistent"]),
                  "under_5000": claude.get("total") is not None and claude["total"] < 5000}
            if claude["is_invoice"] and claude.get("invoice_type"):
                ex["invoice_type"] = claude["invoice_type"]
        elif row["category"] == "invoice" or doc_id in fixes:
            continue  # an (audited) invoice nobody labeled: no reliable chain labels
        else:  # an RVL non-invoice: never to be approved
            ex = {"is_invoice": False, "approve": False, "amount_consistent": False, "under_5000": False,
                  "payable": False}
        out.append(Example(doc_id, doc_id, ex))
    return out


def end_to_end(compiled, held_out: list[Example], cache: AnswerCache) -> tuple[str, dict]:
    """Replay the compiled chain through the Decision monad; compare with the final approve label."""
    counts = {"approved_right": 0, "approved_wrong": 0, "blocked": 0, "stopped_right": 0, "stopped_wrong": 0}
    where = {}
    for ex in held_out:
        decision = compiled.run(ex.input, cache, ex.id)
        should = ex.labels["approve"]
        if decision.ok:
            counts["approved_right" if should else "approved_wrong"] += 1
            continue
        failed = next(e for e in decision.trace if e.status == "failed")
        low = "Confidence too low" in (decision.error or "")
        if low:
            counts["blocked"] += 1
            where[failed.name] = where.get(failed.name, 0) + 1
        else:
            counts["stopped_wrong" if should else "stopped_right"] += 1
    n = len(held_out)
    should_approve = sum(1 for e in held_out if e.labels["approve"])
    lines = ["### End to end on held-out documents (Decision monad replay)", "",
             f"{n} documents; {should_approve} should be approved per Claude's labels.", "",
             "| outcome | count | share |", "|---|---|---|"]
    names = {"approved_right": "auto-approved, correct", "approved_wrong": "**auto-approved, wrong (silent error)**",
             "blocked": "blocked for review (low confidence)", "stopped_right": "stopped, correct (not approvable)",
             "stopped_wrong": "stopped, wrong (approvable invoice rejected)"}
    lines += [f"| {names[k]} | {v} | {v / n:.0%} |" for k, v in counts.items()]
    lines += ["", "Blocked at step: " + (", ".join(f"{k} {v}" for k, v in where.items()) or "none"), ""]
    return "\n".join(lines) + "\n", counts


def agreement() -> str:
    first = claude_labels()
    second_path = LABELS / "second_pass.jsonl"
    if not second_path.exists():
        return "Labeler agreement: second pass not available.\n"
    second = [json.loads(line) for line in second_path.open() if line.strip()]
    lines = ["### Claude labeler agreement (independent second pass)", "",
             "| field | agree | of |", "|---|---|---|"]
    for field in ("is_invoice", "invoice_type", "amount_consistent", "total", "approve"):
        pairs = [(first[r["doc_id"]].get(field), r.get(field)) for r in second if r["doc_id"] in first]
        lines.append(f"| {field} | {sum(a == b for a, b in pairs)} | {len(pairs)} |")
    return "\n".join(lines) + "\n"


def main(budgets: list[float], stop_budget: float = 0.25) -> None:
    for split in ("validation", "test"):
        TEXTS.update(load(split).set_index("doc_id").text.to_dict())
    labels = claude_labels()
    cache = AnswerCache(None)
    calibration = examples("bal120", cache, labels)
    held_out = examples("chain_ver", cache, labels) if run_path(VARIANT, "chain_ver").exists() else []
    out = ["# Full invoice chain: compiled on Claude labels", "",
           f"Calibration: {len(calibration)} docs from bal120 ({sum(1 for e in calibration if e.labels['is_invoice'])} "
           f"invoices per labels). Held-out: {len(held_out)} docs from chain_ver. Claude labels: {len(labels)} docs. "
           f"Stop (miss) budget per step: {stop_budget:.0%}.", "", agreement()]
    for budget in budgets:
        compiler = Compiler(spec(stop_budget), backend=lambda *a: (_ for _ in ()).throw(RuntimeError("cached only")),
                            asymmetric=True)
        compiler.cache = cache
        compiled = compiler.compile(calibration, error_budget=budget, sequential=True)
        out += [f"## Chain budget {budget:.0%}", "", compiled.report().replace("# Calibration report", "### Calibration report"), ""]
        if held_out:
            out += [compiled.verify(held_out, cache).replace("# Verification", "### Per-step verification"), ""]
            text, _ = end_to_end(compiled, held_out, cache)
            out.append(text)
        out += ["```json", json.dumps(compiled.to_json(), indent=2), "```", ""]
    text = "\n".join(out)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "compile__full_chain.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main([float(b) for b in sys.argv[1:]] or [0.10, 0.20])
