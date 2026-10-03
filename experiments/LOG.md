# Experiment log: Clef-Flash confidence on real OCR'd documents

Goal: find out whether Clef-Flash's confidence can be trusted enough to drive the Decision
monad's gate (pass if confidence ≥ τ, else block), and adjust the pipeline until it can.

## Setup

- **Model:** Cloudflare/clef-flash (Qwen3.5-9B backbone + joint schema head), local, CPU only
  (Ryzen 5 7600, 6 cores, AVX-512 BF16, 30 GB RAM), bf16. Batch size 1: batching was slower on
  CPU (6.7 s/doc at bs=1 vs 14.8 at bs=4 vs 20.0 at bs=8, measured on 8 docs), because of padding
  plus the reference (non-fused) linear-attention kernels.
- **Dataset:** [HAMMALE/rvl_cdip_OCR](https://huggingface.co/datasets/HAMMALE/rvl_cdip_OCR):
  RVL-CDIP scanned business documents (1980s-90s tobacco litigation archive, 16 balanced
  classes) with Tesseract OCR. Text = `ocr_paragraphs` joined, capped at 600 words
  (`ocr_words` is truncated to ~100 words, so it isn't used). The OCR is very noisy, which is the
  point: it's the "real scanned invoice" case.
- **Task:** binary "is this an invoice?" (RVL-CDIP label `invoice` vs the 15 other classes).
  Harder than it sounds: budgets, forms, and purchase-order-like forms share invoice vocabulary.
- **Samples:**
  - `dev`: validation split, all 126 invoices + 20 random docs from each of the other 15
    classes = 426 docs (29.6% invoices). Used for every tuning decision.
  - `test`: full test split, 2,056 docs, 127 invoices (6.2%, natural RVL-CDIP prior).
    Touched only for the baseline and the final pipeline.
- **Raw outputs:** every run stores per-doc logits and probabilities in
  `experiments/runs/<variant>__<sample>.jsonl`, so recalibration and thresholds can be fitted
  offline without re-running the model.
- **Metrics** (`experiments/metrics.py`): accuracy, P/R/F1 for invoice, AUROC, average
  precision, Brier, NLL, top-label ECE (10 bins), reliability table, and the **gate table**:
  for τ, coverage (share of docs that pass), selective accuracy (accuracy among passed),
  **silent errors** (wrong AND passed: the thing the monad exists to prevent), split into
  false invoices and missed invoices.

What "proper results" means here: at some τ the gate lets through a useful share of documents
with very few silent errors, and the τ picked on dev holds on test.

## Experiments

### E0 · v0_baseline on dev (2026-10-03)

**Setup:** state = raw OCR text; one question `is_invoice` (noul, "Is this document an invoice?"),
exactly as in `demo.py`. 426 docs, 4.9 s/doc, ~35 min. Full report:
[results/v0_baseline__dev.md](results/v0_baseline__dev.md).

| acc | precision | recall | F1 | AUROC | AP | Brier | NLL | ECE |
|---|---|---|---|---|---|---|---|---|
| 0.808 | 0.978 | **0.357** | 0.523 | 0.927 | 0.853 | 0.165 | 0.612 | **0.162** |

**Findings:**
1. **The errors are almost all on one side.** Only 1 false invoice (a budget) in 300 non-invoices,
   but 81 of 126 invoices are called "not invoice". The median invoice gets p=0.156, and
   **36.5% of real invoices get p < 0.05**. Some of the worst get 0.007.
2. **Reliability is badly skewed at the low end.** Docs scored 0.1-0.2 are 87.5% invoices,
   0.2-0.3 are 100%. Above 0.5 the model is honest (0.9-1.0 bin: mean p 0.953, observed 0.962).
   Clef's "yes" can be trusted; its "no" can't.
3. **The monad gate as built doesn't work.** At τ=0.9 it passes 88% of docs with 54
   silent errors, 53 of them confidently missed invoices. Only τ=0.995 gets silent errors under
   1%, and then it passes 7% of docs and auto-accepts 0 invoices.
4. **Ranking is decent** (AUROC 0.93), so there's signal; it's the calibration (mostly the
   location of the boundary) that's off. Platt scaling (5-fold CV on dev) fixes average
   calibration (ECE 0.162 → 0.043) and gives a usable gate: τ=0.94 passes 33% of docs with
   1 silent error and auto-accepts 51/126 invoices. The confidently scored invoices at
   p≈0.01 remain unrecoverable by any monotone recalibration.
5. Mean p_invoice by true class: invoice 0.368, budget 0.084, file folder 0.031, all others ≤ 0.015.
   Budgets are the only real near-miss class.

**What it means for the monad:** in an approval chain, a wrong pass is almost always "rejected
a real invoice" rather than "approved a non-invoice". The costly direction (paying something that
isn't an invoice) is already rare. The thing to fix is recall: the model under-calls invoices on
noisy OCR.

**Protocol change (user request):** screening moves to `bal120`, a balanced set from the
validation split: 60 random invoices + 4 docs from each of the 15 other classes = 120 docs,
50% invoices. Rationale: what matters for the approval chain is how invoices are handled, and at
the natural 6% prior most compute goes to easy non-invoices. (A first try, `dev10` = stratified
10% with natural prior, had only 13 invoices; on it the baseline *looked* fine, acc 0.951 and
ECE 0.030, because it's dominated by easy "no"s, while auto-accepting 0/13 invoices at a safe
τ. It was dropped.) All 120 bal120 docs are inside `dev`, so E0 results are reused. Because
bal120 is 50/50, accuracy and ECE here aren't comparable to natural-prior numbers; compare
variants on invoice recall, AUROC, false invoices and invoices auto-accepted at a safe τ.

### E0b · v0_baseline on bal120 (reused from E0)

| recall | precision | AUROC | ECE | @τ=0.9 accepted / false / confidently missed | safe τ | invoices auto-accepted at safe τ |
|---|---|---|---|---|---|---|
| 0.367 | 0.957 | 0.921 | 0.276 | 11 / 1 / 23 | 0.995 | **0 / 60** |

Platt (CV) brings ECE to 0.065 but still no τ reaches ≤1% silent errors.

### E1 · v1_criteria on bal120: define what counts as an invoice

**Change:** same raw OCR state; the `is_invoice` noul gets `criteria` describing `true` (vendor
bill requesting payment: invoice no./date, bill-to/remit-to, line items, amounts, total due,
payment terms) and `false` (letters, memos, forms, budgets, purchase orders, ...).

| variant | recall | precision | AUROC | ECE | @τ=0.9 acc / false / missed | safe τ | safe acc / false |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.367 | 0.957 | 0.921 | 0.276 | 11 / 1 / 23 | 0.995 | 0 / 0 |
| **v1_criteria** | **0.700** | 0.933 | 0.934 | **0.084** | 21 / 1 / **0** | 0.965 | 6 / 0 |

**Findings:**
1. **Biggest single win so far.** Recall roughly doubles (0.37 → 0.70), and the confidently
   rejected invoices at τ=0.9 drop from 23 to **0**. The invoices the model is unsure about now
   score 0.17-0.36 instead of ~0.01, which puts them in the gate's **blocked** zone (sent to a
   human) instead of the silently-rejected zone. That's the behaviour the monad needs.
2. Reliability is now roughly diagonal (0.9-1.0 bin: p 0.952, observed 0.955; 0.4-0.5:
   0.449 vs 0.533). The remaining bias is mild under-confidence around 0.5-0.6 (observed 0.82).
3. Platt on top raises recall further (0.87) but costs precision (0.83); with only 120 docs
   the CV fit is noisy. Not adopted yet.
4. **The one confident "false invoice" is a label error.** validation/1277 is labeled `budget`
   but the OCR reads "EDUCATOR INVOICE … NET TOTAL: $2,348.55 … PLEASE RETURN 1 COPY OF INVOICE
   WITH PAYMENT". It's an invoice; Clef (p=0.962) is right. This single doc is what pushes
   the safe τ to 0.965. Tracked in [label_noise.md](label_noise.md); official labels are still
   used in all metrics.

### E2 · v2_framing on bal120: tell the model the text is noisy OCR

**Change:** v1 + state becomes `{"source": "Tesseract OCR of a scanned paper business document
from a 1980s-90s corporate archive. Expect misspellings, merged or garbled tokens, and lost
layout.", "ocr_text": ...}`.

Official labels:

| variant | recall | precision | AUROC | ECE | @τ=0.9 acc / false / missed | safe τ | safe acc / false |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.367 | 0.957 | 0.921 | 0.276 | 11 / 1 / 23 | 0.995 | 0 / 0 |
| v1_criteria | 0.700 | 0.933 | 0.934 | 0.084 | 21 / 1 / 0 | 0.965 | 6 / 0 |
| **v2_framing** | **0.800** | 0.889 | **0.939** | 0.091 | 22 / 1 / 0 | 0.960 | 8 / 0 |

Audited labels (validation/1277 counted as invoice):

| variant | recall | precision | AUROC | ECE | @τ=0.9 acc / false / missed | safe τ | safe acc / false |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.377 | 1.000 | 0.937 | 0.268 | 12 / 0 / 23 | 0.995 | 0 / 0 |
| v0_baseline + platt(CV) | 0.820 | 0.893 | 0.935 | 0.060 | 40 / 1 / 0 | 0.920 | 39 / 0 |
| v1_criteria | 0.705 | 0.956 | 0.949 | 0.093 | 22 / 0 / 0 | 0.835 | 27 / 0 |
| **v2_framing** | **0.803** | 0.907 | **0.954** | 0.097 | 23 / 0 / 0 | **0.820** | **29 / 0** |

**Findings:**
1. Framing adds recall (0.70 → 0.80) and a bit of AUROC (0.934 → 0.939), still with zero
   confidently-missed invoices at τ=0.9.
2. The price is 5 extra non-invoices called "invoice" (2 handwritten, email, news article,
   specification), but **all of them score 0.58-0.66**. They sit inside the blocked zone of any
   τ ≥ 0.7, so the gate routes them to review and never auto-approves them. Calibration is
   doing its job: wrong answers come with low confidence.
3. With the one label error corrected, the in-sample safe τ falls to 0.82, and v2 auto-accepts
   29/61 invoices with 0 false invoices. Before the label fix this was masked: a single
   mislabeled doc decided the threshold. Lesson: on 120 docs, the safe-τ metric is fragile
   to one doc; the test-set run is what counts.
4. Platt on the *baseline* also gets to 39 auto-accepted / 0 false (audited), but at the cost
   of fitting 2 parameters on 120 docs; it's a statistical fix of the boundary, while
   v1/v2 fix it without any labeled data. Both get combined in the final pipeline.

### Note · the process is a neuro-symbolic "calibration compiler" (user observation)

What we're doing for `is_invoice` generalises to every neural step of a monadic chain:

1. **Lowering:** decide which steps stay symbolic (guards, parsing, policy) and which become
   Clef questions; keep the neural surface minimal, since only neural steps need calibration.
2. **Per-step calibration:** for each neural step, find the question formulation (criteria,
   framing), the recalibration, and the gate τ on a labeled set. This is the expensive pass
   (E0-E6 here).
3. **Linking:** split the chain's total silent-error budget across steps; per-step τ follows
   (4 steps at 1% each can leak up to ~4% end-to-end).
4. **Verification:** run the compiled chain on held-out data.

The output is a chain with *measured* error rates per step, not just the model's
own confidence. It's specific to the model and domain: a model upgrade means recompiling
against the same labeled sets, which therefore should be kept like a test suite.

### E3 · v3_choice16 on bal120: 16-way document type instead of yes/no (rejected)

**Change:** same framing as v2, but instead of the `is_invoice` noul, one `choice` over the 16
RVL-CDIP classes, each with a one-line description; p_invoice = P(doc_type = invoice).
Hypothesis: contrastive alternatives (budget, form, ...) calibrate better than a lone yes/no.

| variant | recall | precision | AUROC | ECE | @τ=0.9 acc / false / missed | safe τ | safe acc / false |
|---|---|---|---|---|---|---|---|
| v2_framing | **0.800** | 0.889 | **0.939** | 0.091 | 22 / 1 / **0** | 0.960 | 8 / 0 |
| v3_choice16 | 0.600 | 0.973 | 0.922 | 0.155 | 19 / 1 / **10** | 0.995 | 0 / 0 |

**Findings:**
1. **Hypothesis rejected.** The 16-way choice brings back confident misses: 10 invoices rejected
   at τ=0.9 (v2: 0). Missed invoices go mostly to `budget` (12) and `form` (5). Overall
   16-class accuracy is 64%.
2. **Key observation: how each formulation treats documents it can't read.**

   | doc | what it is | v0 | **v2** | v3 |
   |---|---|---|---|---|
   | validation/508 | OCR garbage, no readable words | 0.036 | **0.516** | 0.038 |
   | validation/338 | OCR garbage, no readable words | 0.009 | **0.469** | 0.041 |
   | validation/1588 | "Computation of Assessment" cost allocation (label debatable) | 0.010 | 0.182 | 0.009 |
   | validation/1115 | "Political campaign contribution request" form (label debatable) | 0.014 | 0.226 | 0.010 |

   With v2 the model answers ~0.5 on unreadable input, i.e. "don't know", and the gate
   blocks. The bare question (v0) and the 16-way choice (v3) both answer a confident "no".
   That's exactly the difference between a chain that fails safe and one that fails silently.
   The two debatable docs get 0.18/0.23 under v2: leaning "no" but not confident enough to
   pass τ≥0.82.
3. Platt (CV) repairs v3 partially (36/61 auto-accepted with audited labels), but a recalibrated
   v3 is still worse than v2 on raw AUROC and needs labeled data to get there.

**Decision:** keep the yes/no-with-criteria formulation (v2) as the primary decision. The 16-way
type question goes into v4 only as an extra *signal* for the combination strategies, not as the
decision.

### E-MJ · Does multi-judge voting buy 9s? (offline, from E0-E3 outputs)

Question: if several formulations act as "judges", does majority voting cut errors the way
Condorcet's jury theorem promises (1 judge 95% → 3 judges 99% → ...)? The theorem assumes
**independent** errors. Repeating the *same* Clef call gives identical answers (one deterministic
forward pass), so the only cheap source of diversity is different formulations. Measured on
bal120 with audited labels:

| judge | error rate (threshold 0.5) |
|---|---|
| v0_baseline | 0.317 |
| v1_criteria | 0.167 |
| **v2_framing** | **0.142** |
| v3_choice16 | 0.200 |

Error correlation (φ) between judges: 0.34-0.78; v1/v2 0.72, v1/v3 0.78. 14 of v2's 17 errors
are also v1 errors.

| ensemble | majority error | mean-prob error | AUROC |
|---|---|---|---|
| v1 + v2 + v3 | **0.167** | 0.175 | 0.952 |
| v0 + v1 + v2 | 0.167 | 0.225 | 0.954 |
| all four | 0.167 | 0.200 | 0.952 |
| *Condorcet prediction if v1, v2, v3 were independent* | *0.076* | | |

**Finding:** voting across formulations of the same model is *worse* than the best single
judge (0.167 vs 0.142), because the errors are correlated: the same hard docs (garbled OCR,
debatable labels) fool every formulation. The Condorcet "each judge pair buys a 9" curve does
not hold for prompt-level diversity. Multi-judge needs genuinely different models or inputs
(Clef vs Jev, text vs image), and its gain has to be measured on labeled data, never assumed.
Measured error correlation is therefore a first-class output of the compiler.

**Second constraint on 9s:** certifying a silent-error rate ε at 95% confidence needs about
3/ε gated decisions with zero errors (rule of three): 0.1% → ~3,000; 0.01% → ~30,000;
0.001% → ~300,000 labeled decisions. With 29 auto-accepted invoices and 0 errors, the most we
can claim today is ≤ 9.8%.

### E4 · v4_evidence on bal120: type question + 5 factual sub-questions in one pass

**Change:** v2's state and `is_invoice` question, plus in the same forward pass: `doc_type`
(16-way) and five narrow nouls: `has_total_due`, `has_invoice_ref`, `requests_payment`,
`has_line_items`, `is_purchase_order`. p_invoice is read from `is_invoice`. Prompt ~1.3k tokens,
17.4 s/doc.

| variant (audited labels) | recall | precision | AUROC | ECE | @τ=0.9 acc / false / missed | safe τ | safe acc / false |
|---|---|---|---|---|---|---|---|
| v2_framing | 0.803 | 0.907 | 0.954 | 0.097 | 23 / 0 / 0 | 0.820 | 29 / 0 |
| **v4_evidence** | **0.918** | 0.862 | **0.955** | 0.112 | 23 / 0 / 0 | **0.745** | **35 / 0** |

**Findings:**
1. **Best formulation so far.** Asking the narrow questions alongside makes the `is_invoice`
   answer itself better: recall 0.80 → 0.92, and the in-sample safe gate auto-accepts 35/61
   invoices with 0 false (v2: 29).
2. **Its errors are structurally different.** Error correlation with the other formulations:
   φ = 0.03 (v0), 0.14 (v3), 0.33 (v1), 0.60 (v2), against 0.5-0.78 among v0-v3. The extra
   questions change how the model reads the document, the first sign of the diversity
   multi-judge needs.
3. **Symbolic combination of the sub-answers doesn't help on 120 docs.** Mean of is_invoice and
   doc_type: 10/60 auto-accepted; AND-agreement: 12/60; stacked logistic regression over all 7
   answers (5-fold CV) overfits: 0/60 at a safe gate. The extra signals are useful *inside*
   the forward pass, not as separate features at this sample size.

### C1 · The calibration compiler (`compiler.py`)

The manual process from E0-E4 is now a library (`compiler.py`, 7 tests in
`tests/test_compiler.py`):

- **Spec:** a chain of `NeuralStep` (with candidate formulations), `Guard` and `Map`.
  A `Candidate` maps raw input → SystemOne request, can set its own backend (Clef or Jev), and
  `ensemble(...)` averages members' probabilities (multi-judge as just another candidate).
- **Calibrate:** per neural step, every candidate is scored on labeled examples; the gate τ is
  the one that passes the most decisions while the **95% Clopper-Pearson upper bound** on
  silent errors stays within the step's share of the budget (εᵢ = 1 − (1 − ε)^(1/m) for m
  neural steps). Among gates passing the same decisions the highest τ wins, so the gate never
  certifies confidence levels the data didn't show (a test caught the original lowest-τ rule
  passing a 0.6 when all calibration data was at 0.99).
- **Output:** a `CompiledChain` that runs through the `Decision` monad with the gates baked in,
  a markdown calibration report (per step: formulation, τ, coverage, errors, bound, budget,
  certified or the sample size needed; all candidates tried; pairwise error correlation),
  `verify()` with frozen gates on held-out data, and a JSON artifact.
- **Answers cached** per (step, candidate, example, request hash): recompiling never re-runs the model.

**First compile, `is_invoice` on bal120** (5 formulations + 2 ensembles, from cached runs;
[results/compile__is_invoice__bal120.md](results/compile__is_invoice__bal120.md)):

| budget | chosen | τ | decided | silent errors | 95% bound | status |
|---|---|---|---|---|---|---|
| 1% | v4_evidence | 0.745 | 72/120 (60%) | 0 | 4.08% | UNCERTIFIED: needs ≥299 decided with 0 errors |
| 10% | v2_framing | 0.615 | 90/120 (75%) | 4 | 9.88% | certified |

The compiler reproduces the manual conclusions (v4 best at tight budgets, v0/v3 worst) and adds
the part the manual process lacked: an explicit statement of what can and can't be claimed from
the data. At 1% the answer is "not yet: get ≥299 decided examples".

### C2 · Separate yes/no gates (compiler option `asymmetric=True`)

E0 showed Clef's "yes" and "no" aren't equally trustworthy, yet the gate used one τ for both. The
compiler can now gate each answer of a yes/no step separately (τ_yes, τ_no searched on a 0.01 grid,
strictest pair among equals). A synthetic test shows the extreme case: when yes's are reliable at
0.85 but no's are noisy below 0.98, one gate can only pass the 150 sure no's (bound 1.98%, not
certifiable at 1%), while separate gates pass 650 with 0 errors (bound 0.46%, certified).

On bal120 (`is_invoice`, all formulations, audited labels):

| budget | gates | chosen | gate | decided | errors | 95% bound | status |
|---|---|---|---|---|---|---|---|
| 1% | one | v4_evidence | 0.745 | 72/120 (60%) | 0 | 4.08% | needs ≥299 decided |
| 1% | yes/no | v4_evidence | yes ≥0.66 / no ≥0.75 | 76/120 (63%) | 0 | 3.87% | needs ≥299 decided |
| **5%** | **yes/no** | **v4_evidence** | **yes ≥0.66 / no ≥0.75** | **76/120 (63%)** | **0** | **3.87%** | **certified** |
| 10% | one | v2_framing | 0.615 | 90/120 (75%) | 4 | 9.88% | certified |
| 10% | yes/no | v2_framing | yes ≥0.62 / no ≥0.58 | 94/120 (78%) | 4 | 9.47% | certified |

Real-data gain is modest (+4 decisions per budget). The direction matches E0: the compiler gates
"yes" lower than "no" because Clef's yes is the more reliable answer. First certified result:
**at a 5% budget, `is_invoice` decides 63% of documents automatically with 0 errors and a 95%
bound of 3.87%** (in-sample; held-out verification on `test_bal` is queued).
The pair search was made fast enough to use (27 s → 0.2 s on 1,000 examples) by skipping
the exact bound whenever the observed rate already exceeds the budget, and caching bounds.
