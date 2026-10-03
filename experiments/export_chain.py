"""Export the compiled full chain as JSON for the visualisation page.

    uv run python -m experiments.export_chain 0.30 out.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime

from compiler import AnswerCache, Compiler, samples_needed
from experiments import compile_chain as cc
from experiments.data import load
from experiments.run import run_path


def main(budget: float, out_path: str, stop_budget: float = 0.25) -> None:
    for split in ("validation", "test"):
        cc.TEXTS.update(load(split).set_index("doc_id").text.to_dict())
    labels = cc.claude_labels()
    cache = AnswerCache(None)
    calibration = cc.examples("bal120", cache, labels)
    held_ready = run_path(cc.VARIANT, "chain_ver").exists() and sum(1 for _ in run_path(cc.VARIANT, "chain_ver").open()) >= 85
    atoms_ready = run_path(cc.ATOMS, "chain_atoms").exists() and sum(1 for _ in run_path(cc.ATOMS, "chain_atoms").open()) >= 145
    held_out = cc.examples("chain_ver", cache, labels) if held_ready else []

    compiler = Compiler(cc.spec(stop_budget), backend=None, asymmetric=True)
    compiler.cache = cache
    compiled = compiler.compile(calibration, error_budget=budget, sequential=True)

    steps = []
    for step in compiler.neural_steps():
        r = compiled.results[step.name]
        g = r.gate
        steps.append({
            "name": step.name, "kind": step.kind, "source": cc.SOURCE[step.name], "gate": g.describe(),
            "reaching": g.n, "decided": g.passed, "continued_ok": g.useful, "false_continues": g.errors,
            "bound": g.bound, "budget": r.budget, "wrong_stops": g.wrong_stops, "miss_rate": g.stop_rate,
            "certified": r.certified, "needed": samples_needed(r.budget, compiled.confidence),
            "pending": cc.SOURCE[step.name] == cc.ATOMS and not atoms_ready,
        })
    e2e = None
    per_step = {s["name"]: {"blocked": 0, "stopped_right": 0, "stopped_wrong": 0} for s in steps}
    if held_out:
        _, counts = cc.end_to_end(compiled, held_out, cache)
        e2e = counts | {"n": len(held_out), "should_approve": sum(1 for e in held_out if e.labels["approve"])}
        for ex in held_out:  # where in the chain each held-out document left it
            decision = compiled.run(ex.input, cache, ex.id)
            if decision.ok:
                continue
            failed = next(e for e in decision.trace if e.status == "failed")
            if "Confidence too low" in (decision.error or ""):
                per_step[failed.name]["blocked"] += 1
            else:
                per_step[failed.name]["stopped_wrong" if ex.labels["approve"] else "stopped_right"] += 1
    for s in steps:
        s["held_out"] = per_step[s["name"]]
    first = cc.claude_labels()
    second = [json.loads(line) for line in (cc.LABELS / "second_pass.jsonl").open() if line.strip()]
    agree = {f: [sum(first[r["doc_id"]].get(f) == r.get(f) for r in second if r["doc_id"] in first), len(second)]
             for f in ("is_invoice", "invoice_type", "amount_consistent", "approve")}
    rows = list(labels.values())
    data = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "budget": budget, "stop_budget": stop_budget,
        "chain_bound": compiled.chain_bound(), "certified": compiled.certified(), "steps": steps,
        "end_to_end": e2e, "held_ready": held_ready, "atoms_ready": atoms_ready,
        "calibration_docs": len(calibration), "heldout_docs": len(held_out),
        "labels": {"labeled": len(rows), "invoices": sum(r["is_invoice"] for r in rows),
                   "approvable": sum(r["approve"] for r in rows), "agreement": agree},
    }
    with open(out_path, "w") as sink:
        json.dump(data, sink, indent=1)
    print(json.dumps({k: v for k, v in data.items() if k != "steps"}, indent=1))
    for s in steps:
        print(s["name"], s["reaching"], s["continued_ok"], s["false_continues"], round(s["bound"], 3), s["pending"])


if __name__ == "__main__":
    main(float(sys.argv[1]), sys.argv[2])
