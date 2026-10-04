# calibrated-chains

Neural System One meets a symbolic monad, plus a compiler that turns the combination into a chain with
**measured, budgeted error rates**.

- **Neural:** [Clef-Flash](https://huggingface.co/Cloudflare/clef-flash) (Qwen3.5-9B backbone + joint schema
  head) answers typed questions (`noul` / `choice` / `score`) with probabilities in one forward pass.
  Jev (TypeSafe API) serves the same request/response contract over HTTP.
- **Symbolic:** `Decision` (`clef_monad.py`) sequences those answers, gates them on confidence and rules, and
  keeps an audit trace. The first failure short-circuits the chain.
- **Compiler:** `compiler.py` picks, per neural step, the question formulation and the confidence gate that
  keep silent errors (confident AND wrong) within a budget, using labeled examples, and verifies the
  result on held-out data.

## High-level flow

```
            chain spec                      labeled examples          error budget
  (NeuralStep / Guard / Map,           (calibration + held-out)     (e.g. 30% at 95%)
   candidate formulations)                        │                        │
               │                                  │                        │
               └──────────────┬───────────────────┴────────────────────────┘
                              ▼
               ┌───────────────────────────────┐
               │  Compiler.compile()           │   for each neural step, in order:
               │                               │    1. ask Clef/Jev every candidate (cached)
               │                               │    2. per candidate, find gate τ (or τ_yes/τ_no)
               │                               │       whose 95% upper bound on silent errors
               │                               │       fits the step's share of the budget
               │                               │    3. keep the candidate that decides most
               └───────────────┬───────────────┘
                               ▼
               CompiledChain: formulation + gate per step,
               calibration report, JSON artifact
                               │
              ┌────────────────┼────────────────┐
              ▼                                 ▼
   compiled.verify(held_out)          compiled.run(document)
   frozen gates on unseen data        → Decision monad:
   → does the budget hold?              pure → bind → guard → … → map
                                        each step: pass / BLOCKED (review) / stop
                                        + audit trace
```

The idea in one sentence: **the model's confidence is not trusted as-is; each gate's threshold is
earned on labeled data, and the chain states what it can and can't claim.**

### At runtime: a document through the monad

```
document ─▶ is_invoice ─▶ invoice_type ─▶ amount_consistent ─▶ under_5000 ─▶ payable ─▶ decide
              (neural)      (neural)          (neural)           (neural)     (neural)   (symbolic)
                 │
     confident "yes"  → continue
     confident "no"   → stop (correct non-approval, logged)
     below the gate   → BLOCKED: sent to a human; every later step is recorded as SKIPPED, never run
```

APPROVE happens only when every gate passes. A shaky "yes" can't turn into an approval further down.

## Pieces

| file | role |
|---|---|
| `clef_monad.py` | `Decision` = Either (ok / blocked) × Writer (audit trace). `noul` / `choice` / `score` steps, `bind`, `guard`, `map`, `render`. Default bands: high ≥ 85%, medium ≥ 70%, lower blocks. |
| `clef_backend.py` | Local Clef-Flash on CPU (bf16). A backend is `(state, questions) -> answers`. |
| `jev_backend.py` | Jev over HTTP, same contract (`JEV` key in env or `.env`). |
| `compiler.py` | The calibration compiler (below). |
| `demo.py` | Invoice-approval demo on three synthetic documents, with a confidence-blind pipeline for contrast. |
| `experiments/` | Runs, metrics, and compile scripts on real scanned documents; [`LOG.md`](experiments/LOG.md) is the full lab notebook. |
| `labels/` | Claude-made silver labels for the full chain ([`GUIDE.md`](labels/GUIDE.md) is the labeling guide). |
| `tests/` | Monad and compiler tests with a fake backend; no model needed. |

### The Decision monad

```python
Decision.pure(doc)
    .bind(noul(backend, "is_invoice", "Is this document an invoice?"))
    .bind(choice(backend, "invoice_type", "What type of invoice?", {...}))
    .guard("amount_ok", lambda ctx: ctx["amount_reasonable"] >= 5.0)
    .map("decide", lambda ctx: {"action": "APPROVE"})
```

Each Clef question is a Kleisli arrow: `bind` gates on confidence, `guard` on rules, `map` builds the
result. `ctx` accumulates the input plus every typed answer so far.

### The calibration compiler

```python
spec = [
    NeuralStep("is_invoice", "noul", candidates=[Candidate("bare", bare), Candidate("criteria", crit)]),
    Guard("amount_ok", lambda ctx: ctx["amount"] >= 2.0),
    NeuralStep("approve", "noul", candidates=[...]),
    Map("decide", lambda ctx: {"action": "APPROVE"}),
]
compiled = Compiler(spec, backend, asymmetric=True).compile(calibration_set, error_budget=0.01, sequential=True)
print(compiled.report())              # per step: formulation, gate, coverage, errors, bound, certified?
compiled.run(doc)                     # a Decision with the gates baked in
print(compiled.verify(held_out_set))  # frozen gates on unseen data
```

What it does:

- **Candidates.** A step lists alternative formulations (wording, criteria, framing, text vs image,
  Clef vs Jev). `ensemble(...)` averages members' probabilities, so multi-judge voting is just another
  candidate and has to win on data.
- **Budget split.** The chain budget ε is split over m neural steps: εᵢ = 1 − (1 − ε)^(1/m). Symbolic
  steps are exact and cost nothing.
- **Gate search.** The gate is the lowest τ (on a grid starting above 0.5) whose 95% Clopper-Pearson
  upper bound on silent errors fits εᵢ; ties go to the higher τ. With `asymmetric=True`, yes/no steps get
  separate τ_yes / τ_no.
- **What counts as an error.** `budget_on="continue"` budgets only wrong answers that let the chain
  continue toward an action; `stop_budget` bounds the miss rate (should-continue inputs confidently
  stopped). `priors=` reweights to the production class mix, with bounds on the Kish effective sample size.
- **Sequential.** With `sequential=True`, each step is calibrated (and verified) on the examples the
  earlier compiled gates actually let through.
- **Honest output.** A step that can't be certified is still compiled, flagged UNCERTIFIED, with the
  sample size it would need. The report also lists every candidate tried and their pairwise error
  correlation.
- **Cache.** Answers are cached per (step, candidate, example, request hash; images hashed by content),
  so recompiling never re-runs the model.

## Results so far

Dataset: [RVL-CDIP OCR](https://huggingface.co/datasets/HAMMALE/rvl_cdip_OCR), 1980s-90s scanned
business documents with noisy Tesseract OCR. Clef-Flash on CPU. Details and every number are in
[`experiments/LOG.md`](experiments/LOG.md).

**`is_invoice` alone (bal120: 60 invoices + 60 others):**

| step | change | effect |
|---|---|---|
| E0 | bare question | Clef's "yes" is trustworthy, its "no" isn't: 36% of real invoices scored p < 0.05 |
| E1-E2 | criteria + "this is noisy OCR" framing | recall 0.37 → 0.80; unreadable docs score ~0.5 ("don't know") instead of a confident "no" |
| E3 | 16-way doc-type choice | rejected: confident misses come back |
| E-MJ | voting over rewordings | worse than the best single judge; errors are correlated (φ 0.34-0.78) |
| E4 | extra factual sub-questions in the same pass | recall 0.92, best text formulation |
| E5 | scan image + OCR | AUROC 0.992; error correlation with text-only φ = 0.29, so text + image judges vote usefully |
| C4 | compiler, production mix | picks vote(text, image): 54/61 invoices accepted, 0 false accepts, bound 5.4% |

**Full chain** (C5; labels from Claude, 100 docs, 79/80 agreement on a second pass):
`is_invoice → invoice_type → amount_consistent → under_5000 → payable → decide`, 30% chain budget,
sequential, yes/no gates. Held-out, 85 documents, through the monad:

| outcome | docs |
|---|---|
| auto-approved, correct | 2 |
| **auto-approved, wrong** | **0** |
| blocked for review | 38 |
| stopped, correct | 41 |
| stopped, wrong (approvable invoice rejected) | 4 |

The chain fails safe but is **not certified**: the data funnel (119 calibration docs → 4 reaching the
last gate) can't support a tight bound. Certifying at 30% needs ~250 approvable invoices across
calibration. Two lessons from getting here:

1. A single policy question ("should this be approved?") didn't calibrate; it was **lowered** into atomic
   conditions joined by a symbolic AND.
2. RVL-CDIP's `invoice` class is ~37% checks, remittance stubs and vouchers, so labels matter more than
   formulation tweaks.

Schematic of the compiled chain: <https://claude.ai/artifact/M4VrnWbSwcor7fkr62Dt1E>.

## Run

```bash
uv sync
uv run pytest                                                     # monad + compiler tests, no model needed

hf download Cloudflare/clef-flash --local-dir models/clef-flash   # ~18 GB
uv run python demo.py --naive        # CPU works: ~14 GB RAM, ~6 s per decision
uv run python demo.py --jev --naive  # same pipeline on Jev (key as JEV in .env)
```

Experiments (need the dataset parquet files in `data/rvl_cdip_ocr/data/`):

```bash
hf download HAMMALE/rvl_cdip_OCR --repo-type dataset --local-dir data/rvl_cdip_ocr

uv run python -m experiments.run v4_evidence bal120          # run a variant with Clef (resumable JSONL in experiments/runs/)
experiments/queue.sh bal120 v1_criteria v2_framing           # several variants, one model in RAM at a time
uv run python -m experiments.report v4_evidence bal120       # metrics + gate table → experiments/results/
uv run python -m experiments.compare bal120                  # one row per finished variant

uv run python -m experiments.compile_invoice bal120:test_bal 0.05 0.10   # compile is_invoice, verify held-out
uv run python -m experiments.compile_chain 0.30                          # compile + verify the full chain
uv run python -m experiments.export_chain 0.30 chain.json                # data for the schematic
```

The compile scripts replay recorded answers from `experiments/runs/` (committed), so they don't load the model.
