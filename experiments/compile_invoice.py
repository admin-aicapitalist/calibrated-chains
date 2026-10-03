"""Compile the is_invoice step from every formulation measured so far, using cached experiment outputs.

    uv run python -m experiments.compile_invoice bal120 0.01 0.10                # compile only
    uv run python -m experiments.compile_invoice bal120:test_bal 0.01 0.10       # compile, then verify held-out

Candidates are the experiment variants (and ensembles of them) that have a complete run on the sample.
Their answers are seeded into the compiler's cache from experiments/runs, so compiling never calls the
model; a candidate without a run is skipped, not executed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from compiler import AnswerCache, Candidate, Compiler, Example, NeuralStep, ensemble
from experiments.compare import corrections
from experiments.data import load
from experiments.metrics import RESULTS
from experiments.run import run_path
from experiments.variants import VARIANTS

STEP = "is_invoice"
CACHE = Path(__file__).parent / "runs" / "compiler_cache.jsonl"
SINGLES = ["v0_baseline", "v1_criteria", "v2_framing", "v3_choice16", "v4_evidence", "v5_image_text",
           "j_first70", "j_last70", "j_mid70", "j_trim80", "j_inverted", "j_clerk"]
ENSEMBLES = {
    "vote(v1,v2,v3)": ["v1_criteria", "v2_framing", "v3_choice16"],
    "vote(v2,v4)": ["v2_framing", "v4_evidence"],
    "vote(v2,windows)": ["v2_framing", "j_first70", "j_last70", "j_mid70", "j_trim80"],
    "vote(v2,inverted,clerk)": ["v2_framing", "j_inverted", "j_clerk"],
    "vote(v2,v5)": ["v2_framing", "v5_image_text"],
}


def question_id(variant: str) -> str:
    return {"v3_choice16": "doc_type", "j_inverted": "not_invoice"}.get(variant, STEP)


def readout(variant: str):
    """Map the variant's answer onto is_invoice yes/no probabilities."""
    if variant == "v3_choice16":
        return lambda a: {"true": a["probabilities"]["invoice"], "false": 1 - a["probabilities"]["invoice"]}
    if variant == "j_inverted":
        return lambda a: {"true": 1 - a["noul"], "false": a["noul"]}
    return None


def p_invoice(row: dict, variant: str) -> float:
    answer = row["answers"][question_id(variant)]
    probs = dict(zip(answer["options"], answer["probs"]))
    return {"doc_type": probs.get("invoice"), "not_invoice": probs.get("false")}.get(question_id(variant), probs.get("true"))


def candidate(variant: str) -> Candidate:
    return Candidate(variant, build=VARIANTS[variant], question_id=question_id(variant), readout=readout(variant))


def no_model(state, questions):
    raise RuntimeError("compile_invoice runs from cached outputs only; run the variant first")


def load_sample(sample_name: str, cache: AnswerCache) -> tuple[list[Example], list[str]]:
    """Examples for every doc that all complete text runs on this sample share; seeds the cache."""
    texts = {}
    for split in ("validation", "test"):
        texts |= load(split).set_index("doc_id").text.to_dict()
    fixes = corrections()
    rows_by = {}
    for variant in SINGLES:
        path = run_path(variant, sample_name)
        if path.exists() and not getattr(VARIANTS[variant], "needs_image", False):
            rows_by[variant] = {r["doc_id"]: r for r in map(json.loads, path.open())}
    if not rows_by:
        return [], []
    n = max(len(r) for r in rows_by.values())
    available = [v for v in rows_by if len(rows_by[v]) == n]
    ids = sorted(rows_by[available[0]])
    for variant in available:
        for i in ids:
            p = p_invoice(rows_by[variant][i], variant)
            cache.data[AnswerCache.key(STEP, variant, i, VARIANTS[variant](texts[i]))] = {"true": p, "false": 1 - p}
    labels = {i: fixes.get(i, rows_by[available[0]][i]["category"] == "invoice") for i in ids}
    return [Example(i, texts[i], {STEP: labels[i]}) for i in ids], available


def main(samples: str, budgets: list[float]) -> None:
    calib_name, _, verify_name = samples.partition(":")
    cache = AnswerCache(None)
    examples, available = load_sample(calib_name, cache)
    held_out, verifiable = load_sample(verify_name, cache) if verify_name else ([], [])
    singles = [candidate(v) for v in available]
    by_name = {c.name: c for c in singles}
    votes = [ensemble(name, *(by_name[m] for m in members)) for name, members in ENSEMBLES.items()
             if all(m in by_name for m in members)]
    spec = [NeuralStep(STEP, "noul", singles + votes)]

    out = [f"# Compiling `{STEP}` on {calib_name}" + (f", verifying on {verify_name}" if verify_name else ""), "",
           f"{len(examples)} labeled calibration docs (audited labels), {len(singles)} single formulations, "
           f"{len(votes)} ensembles. Not available as text runs on {calib_name}: "
           f"{', '.join(v for v in SINGLES if v not in by_name) or 'none'}.", ""]
    if verify_name:
        out += [f"Held-out {verify_name}: {len(held_out)} docs; formulations with runs there: {', '.join(verifiable)}.", ""]
    for budget, asymmetric in [(b, a) for b in budgets for a in (False, True)]:
        compiler = Compiler(spec, backend=no_model, asymmetric=asymmetric)
        compiler.cache = cache
        compiled = compiler.compile(examples, error_budget=budget)
        mode = "separate yes/no gates" if asymmetric else "one gate"
        out += [f"## Budget {budget:.0%}, {mode}", "", compiled.report().replace("# Calibration report", "### Report"), ""]
        if verify_name:
            chosen = compiled.results[STEP].chosen
            members = [m.name for m in chosen.members] or [chosen.name]
            if all(m in verifiable for m in members):
                out += [compiled.verify(held_out, cache).replace("# Verification", "### Verification"), ""]
            else:
                out += [f"### Verification: skipped, {chosen.name} has no complete run on {verify_name} yet", ""]
        out += ["```json", json.dumps(compiled.to_json(), indent=2), "```", ""]
    text = "\n".join(out)
    RESULTS.mkdir(exist_ok=True)
    suffix = f"{calib_name}" + (f"__verify_{verify_name}" if verify_name else "")
    (RESULTS / f"compile__{STEP}__{suffix}.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main(sys.argv[1], [float(b) for b in sys.argv[2:]] or [0.01, 0.10])
