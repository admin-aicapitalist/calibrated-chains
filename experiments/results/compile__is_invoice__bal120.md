# Compiling `is_invoice` on bal120

120 labeled calibration docs (audited labels), 5 single formulations, 2 ensembles. Not available as text runs on bal120: v5_image_text, j_first70, j_last70, j_mid70, j_trim80, j_inverted, j_clerk.

## Budget 1%, one gate, sample mix

### Report

Chain error budget **1.00%** silent errors at 95% confidence, split over 1 neural step(s) (1.000% each). Symbolic steps are exact.

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | v4_evidence | 0.655 | 81/120 (68%) | 40 | 0 | 0.00% | 7.22% | 1.00% | 2 | UNCERTIFIED: needs ≥299 continued (accepted) decisions, 0 errors; missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (over the 1.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.990 | 37/120 | 0 | 0 | 100.00% | 2 | no |
| v1_criteria | 0.745 | 75/120 | 31 | 0 | 9.21% | 2 | no |
| v2_framing | 0.665 | 81/120 | 37 | 0 | 7.78% | 2 | no |
| v3_choice16 | 0.965 | 43/120 | 1 | 0 | 95.00% | 2 | no |
| v4_evidence ← chosen | 0.655 | 81/120 | 40 | 0 | 7.22% | 2 | no |
| vote(v1,v2,v3) | 0.745 | 76/120 | 31 | 0 | 9.21% | 2 | no |
| vote(v2,v4) | 0.660 | 79/120 | 38 | 0 | 7.58% | 2 | no |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.01,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "v4_evidence",
      "gate": {
        "*": 0.655
      },
      "decided": 81,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.010000000000000009,
      "certified": false
    }
  }
}
```

## Budget 1%, one gate, production mix (1/16 invoices)

### Report

Chain error budget **1.00%** silent errors at 95% confidence, split over 1 neural step(s) (1.000% each). Symbolic steps are exact.

Rates and coverage are reweighted to the production label mix (is_invoice: True=6%, False=94%); bounds use the effective sample size of the decided examples (ESS).

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | v4_evidence | 0.655 | 81/120 (66%) | 40 | 0 | 0.00% | 7.22% | 1.00% | 2 | UNCERTIFIED: needs ≥299 continued (accepted) decisions, 0 errors (ESS 40); missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (over the 1.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.990 | 37/120 | 0 | 0 | 100.00% | 2 | no |
| v1_criteria | 0.745 | 75/120 | 31 | 0 | 9.21% | 2 | no |
| v2_framing | 0.665 | 81/120 | 37 | 0 | 7.78% | 2 | no |
| v3_choice16 | 0.965 | 43/120 | 1 | 0 | 95.00% | 2 | no |
| v4_evidence ← chosen | 0.655 | 81/120 | 40 | 0 | 7.22% | 2 | no |
| vote(v1,v2,v3) | 0.745 | 76/120 | 31 | 0 | 9.21% | 2 | no |
| vote(v2,v4) | 0.660 | 79/120 | 38 | 0 | 7.58% | 2 | no |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.01,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "v4_evidence",
      "gate": {
        "*": 0.655
      },
      "decided": 81,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.010000000000000009,
      "certified": false
    }
  }
}
```

## Budget 1%, separate yes/no gates, sample mix

### Report

Chain error budget **1.00%** silent errors at 95% confidence, split over 1 neural step(s) (1.000% each). Symbolic steps are exact.

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | vote(v1,v2,v3) | true ≥0.50 / false ≥0.75 | 85/120 (71%) | 40 | 0 | 0.00% | 7.22% | 1.00% | 2 | UNCERTIFIED: needs ≥299 continued (accepted) decisions, 0 errors; missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (over the 1.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | true ≥0.50 / false ≥0.99 | 60/120 | 23 | 0 | 12.21% | 2 | no |
| v1_criteria | true ≥0.57 / false ≥0.75 | 80/120 | 37 | 0 | 7.78% | 1 | no |
| v2_framing | true ≥0.67 / false ≥0.65 | 82/120 | 37 | 0 | 7.78% | 2 | no |
| v3_choice16 | true ≥0.50 / false ≥0.97 | 77/120 | 37 | 0 | 7.78% | 2 | no |
| v4_evidence | true ≥0.66 / false ≥0.62 | 82/120 | 39 | 0 | 7.39% | 2 | no |
| vote(v1,v2,v3) ← chosen | true ≥0.50 / false ≥0.75 | 85/120 | 40 | 0 | 7.22% | 2 | no |
| vote(v2,v4) | true ≥0.66 / false ≥0.64 | 82/120 | 38 | 0 | 7.58% | 2 | no |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.01,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "vote(v1,v2,v3)",
      "gate": {
        "true": 0.5,
        "false": 0.75
      },
      "decided": 85,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.010000000000000009,
      "certified": false
    }
  }
}
```

## Budget 1%, separate yes/no gates, production mix (1/16 invoices)

### Report

Chain error budget **1.00%** silent errors at 95% confidence, split over 1 neural step(s) (1.000% each). Symbolic steps are exact.

Rates and coverage are reweighted to the production label mix (is_invoice: True=6%, False=94%); bounds use the effective sample size of the decided examples (ESS).

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | vote(v1,v2,v3) | true ≥0.50 / false ≥0.75 | 85/120 (73%) | 40 | 0 | 0.00% | 7.22% | 1.00% | 2 | UNCERTIFIED: needs ≥299 continued (accepted) decisions, 0 errors (ESS 40); missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (over the 1.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | true ≥0.50 / false ≥0.99 | 60/120 | 23 | 0 | 12.21% | 2 | no |
| v1_criteria | true ≥0.57 / false ≥0.75 | 80/120 | 37 | 0 | 7.78% | 1 | no |
| v2_framing | true ≥0.67 / false ≥0.65 | 82/120 | 37 | 0 | 7.78% | 2 | no |
| v3_choice16 | true ≥0.50 / false ≥0.97 | 77/120 | 37 | 0 | 7.78% | 2 | no |
| v4_evidence | true ≥0.66 / false ≥0.62 | 82/120 | 39 | 0 | 7.39% | 2 | no |
| vote(v1,v2,v3) ← chosen | true ≥0.50 / false ≥0.75 | 85/120 | 40 | 0 | 7.22% | 2 | no |
| vote(v2,v4) | true ≥0.66 / false ≥0.64 | 82/120 | 38 | 0 | 7.58% | 2 | no |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.01,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "vote(v1,v2,v3)",
      "gate": {
        "true": 0.5,
        "false": 0.75
      },
      "decided": 85,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.010000000000000009,
      "certified": false
    }
  }
}
```

## Budget 5%, one gate, sample mix

### Report

Chain error budget **5.00%** silent errors at 95% confidence, split over 1 neural step(s) (5.000% each). Symbolic steps are exact.

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | v4_evidence | 0.655 | 81/120 (68%) | 40 | 0 | 0.00% | 7.22% | 5.00% | 2 | UNCERTIFIED: needs ≥59 continued (accepted) decisions, 0 errors; missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (over the 5.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.990 | 37/120 | 0 | 0 | 100.00% | 2 | no |
| v1_criteria | 0.745 | 75/120 | 31 | 0 | 9.21% | 2 | no |
| v2_framing | 0.665 | 81/120 | 37 | 0 | 7.78% | 2 | no |
| v3_choice16 | 0.965 | 43/120 | 1 | 0 | 95.00% | 2 | no |
| v4_evidence ← chosen | 0.655 | 81/120 | 40 | 0 | 7.22% | 2 | no |
| vote(v1,v2,v3) | 0.745 | 76/120 | 31 | 0 | 9.21% | 2 | no |
| vote(v2,v4) | 0.660 | 79/120 | 38 | 0 | 7.58% | 2 | no |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.05,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "v4_evidence",
      "gate": {
        "*": 0.655
      },
      "decided": 81,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.050000000000000044,
      "certified": false
    }
  }
}
```

## Budget 5%, one gate, production mix (1/16 invoices)

### Report

Chain error budget **5.00%** silent errors at 95% confidence, split over 1 neural step(s) (5.000% each). Symbolic steps are exact.

Rates and coverage are reweighted to the production label mix (is_invoice: True=6%, False=94%); bounds use the effective sample size of the decided examples (ESS).

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | v4_evidence | 0.655 | 81/120 (66%) | 40 | 0 | 0.00% | 7.22% | 5.00% | 2 | UNCERTIFIED: needs ≥59 continued (accepted) decisions, 0 errors (ESS 40); missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (over the 5.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.990 | 37/120 | 0 | 0 | 100.00% | 2 | no |
| v1_criteria | 0.745 | 75/120 | 31 | 0 | 9.21% | 2 | no |
| v2_framing | 0.665 | 81/120 | 37 | 0 | 7.78% | 2 | no |
| v3_choice16 | 0.965 | 43/120 | 1 | 0 | 95.00% | 2 | no |
| v4_evidence ← chosen | 0.655 | 81/120 | 40 | 0 | 7.22% | 2 | no |
| vote(v1,v2,v3) | 0.745 | 76/120 | 31 | 0 | 9.21% | 2 | no |
| vote(v2,v4) | 0.660 | 79/120 | 38 | 0 | 7.58% | 2 | no |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.05,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "v4_evidence",
      "gate": {
        "*": 0.655
      },
      "decided": 81,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.050000000000000044,
      "certified": false
    }
  }
}
```

## Budget 5%, separate yes/no gates, sample mix

### Report

Chain error budget **5.00%** silent errors at 95% confidence, split over 1 neural step(s) (5.000% each). Symbolic steps are exact.

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | vote(v1,v2,v3) | true ≥0.50 / false ≥0.75 | 85/120 (71%) | 40 | 0 | 0.00% | 7.22% | 5.00% | 2 | UNCERTIFIED: needs ≥59 continued (accepted) decisions, 0 errors; missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (over the 5.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | true ≥0.50 / false ≥0.99 | 60/120 | 23 | 0 | 12.21% | 2 | no |
| v1_criteria | true ≥0.57 / false ≥0.75 | 80/120 | 37 | 0 | 7.78% | 1 | no |
| v2_framing | true ≥0.67 / false ≥0.65 | 82/120 | 37 | 0 | 7.78% | 2 | no |
| v3_choice16 | true ≥0.50 / false ≥0.97 | 77/120 | 37 | 0 | 7.78% | 2 | no |
| v4_evidence | true ≥0.66 / false ≥0.62 | 82/120 | 39 | 0 | 7.39% | 2 | no |
| vote(v1,v2,v3) ← chosen | true ≥0.50 / false ≥0.75 | 85/120 | 40 | 0 | 7.22% | 2 | no |
| vote(v2,v4) | true ≥0.66 / false ≥0.64 | 82/120 | 38 | 0 | 7.58% | 2 | no |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.05,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "vote(v1,v2,v3)",
      "gate": {
        "true": 0.5,
        "false": 0.75
      },
      "decided": 85,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.050000000000000044,
      "certified": false
    }
  }
}
```

## Budget 5%, separate yes/no gates, production mix (1/16 invoices)

### Report

Chain error budget **5.00%** silent errors at 95% confidence, split over 1 neural step(s) (5.000% each). Symbolic steps are exact.

Rates and coverage are reweighted to the production label mix (is_invoice: True=6%, False=94%); bounds use the effective sample size of the decided examples (ESS).

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | vote(v1,v2,v3) | true ≥0.50 / false ≥0.75 | 85/120 (73%) | 40 | 0 | 0.00% | 7.22% | 5.00% | 2 | UNCERTIFIED: needs ≥59 continued (accepted) decisions, 0 errors (ESS 40); missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (over the 5.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | true ≥0.50 / false ≥0.99 | 60/120 | 23 | 0 | 12.21% | 2 | no |
| v1_criteria | true ≥0.57 / false ≥0.75 | 80/120 | 37 | 0 | 7.78% | 1 | no |
| v2_framing | true ≥0.67 / false ≥0.65 | 82/120 | 37 | 0 | 7.78% | 2 | no |
| v3_choice16 | true ≥0.50 / false ≥0.97 | 77/120 | 37 | 0 | 7.78% | 2 | no |
| v4_evidence | true ≥0.66 / false ≥0.62 | 82/120 | 39 | 0 | 7.39% | 2 | no |
| vote(v1,v2,v3) ← chosen | true ≥0.50 / false ≥0.75 | 85/120 | 40 | 0 | 7.22% | 2 | no |
| vote(v2,v4) | true ≥0.66 / false ≥0.64 | 82/120 | 38 | 0 | 7.58% | 2 | no |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.05,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "vote(v1,v2,v3)",
      "gate": {
        "true": 0.5,
        "false": 0.75
      },
      "decided": 85,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.050000000000000044,
      "certified": false
    }
  }
}
```

## Budget 10%, one gate, sample mix

### Report

Chain error budget **10.00%** silent errors at 95% confidence, split over 1 neural step(s) (10.000% each). Symbolic steps are exact.

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | v4_evidence | 0.655 | 81/120 (68%) | 40 | 0 | 0.00% | 7.22% | 10.00% | 2 | certified; missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (within the 10.00% budget). Chain CERTIFIED.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.990 | 37/120 | 0 | 0 | 100.00% | 2 | no |
| v1_criteria | 0.745 | 75/120 | 31 | 0 | 9.21% | 2 | yes |
| v2_framing | 0.670 | 81/120 | 37 | 0 | 7.78% | 2 | yes |
| v3_choice16 | 0.965 | 43/120 | 1 | 0 | 95.00% | 2 | no |
| v4_evidence ← chosen | 0.655 | 81/120 | 40 | 0 | 7.22% | 2 | yes |
| vote(v1,v2,v3) | 0.750 | 76/120 | 31 | 0 | 9.21% | 2 | yes |
| vote(v2,v4) | 0.665 | 79/120 | 38 | 0 | 7.58% | 2 | yes |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.1,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "v4_evidence",
      "gate": {
        "*": 0.655
      },
      "decided": 81,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.09999999999999998,
      "certified": true
    }
  }
}
```

## Budget 10%, one gate, production mix (1/16 invoices)

### Report

Chain error budget **10.00%** silent errors at 95% confidence, split over 1 neural step(s) (10.000% each). Symbolic steps are exact.

Rates and coverage are reweighted to the production label mix (is_invoice: True=6%, False=94%); bounds use the effective sample size of the decided examples (ESS).

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | v4_evidence | 0.655 | 81/120 (66%) | 40 | 0 | 0.00% | 7.22% | 10.00% | 2 | certified (ESS 40); missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (within the 10.00% budget). Chain CERTIFIED.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.990 | 37/120 | 0 | 0 | 100.00% | 2 | no |
| v1_criteria | 0.745 | 75/120 | 31 | 0 | 9.21% | 2 | yes |
| v2_framing | 0.670 | 81/120 | 37 | 0 | 7.78% | 2 | yes |
| v3_choice16 | 0.965 | 43/120 | 1 | 0 | 95.00% | 2 | no |
| v4_evidence ← chosen | 0.655 | 81/120 | 40 | 0 | 7.22% | 2 | yes |
| vote(v1,v2,v3) | 0.750 | 76/120 | 31 | 0 | 9.21% | 2 | yes |
| vote(v2,v4) | 0.665 | 79/120 | 38 | 0 | 7.58% | 2 | yes |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.1,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "v4_evidence",
      "gate": {
        "*": 0.655
      },
      "decided": 81,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.09999999999999998,
      "certified": true
    }
  }
}
```

## Budget 10%, separate yes/no gates, sample mix

### Report

Chain error budget **10.00%** silent errors at 95% confidence, split over 1 neural step(s) (10.000% each). Symbolic steps are exact.

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | vote(v1,v2,v3) | true ≥0.50 / false ≥0.75 | 85/120 (71%) | 40 | 0 | 0.00% | 7.22% | 10.00% | 2 | certified; missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (within the 10.00% budget). Chain CERTIFIED.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | true ≥0.50 / false ≥0.99 | 60/120 | 23 | 0 | 12.21% | 2 | no |
| v1_criteria | true ≥0.58 / false ≥0.76 | 80/120 | 37 | 0 | 7.78% | 1 | yes |
| v2_framing | true ≥0.69 / false ≥0.66 | 82/120 | 37 | 0 | 7.78% | 2 | yes |
| v3_choice16 | true ≥0.53 / false ≥0.97 | 77/120 | 37 | 0 | 7.78% | 2 | yes |
| v4_evidence | true ≥0.66 / false ≥0.62 | 82/120 | 39 | 0 | 7.39% | 2 | yes |
| vote(v1,v2,v3) ← chosen | true ≥0.50 / false ≥0.75 | 85/120 | 40 | 0 | 7.22% | 2 | yes |
| vote(v2,v4) | true ≥0.66 / false ≥0.64 | 82/120 | 38 | 0 | 7.58% | 2 | yes |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.1,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "vote(v1,v2,v3)",
      "gate": {
        "true": 0.5,
        "false": 0.75
      },
      "decided": 85,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.09999999999999998,
      "certified": true
    }
  }
}
```

## Budget 10%, separate yes/no gates, production mix (1/16 invoices)

### Report

Chain error budget **10.00%** silent errors at 95% confidence, split over 1 neural step(s) (10.000% each). Symbolic steps are exact.

Rates and coverage are reweighted to the production label mix (is_invoice: True=6%, False=94%); bounds use the effective sample size of the decided examples (ESS).

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | vote(v1,v2,v3) | true ≥0.50 / false ≥0.75 | 85/120 (73%) | 40 | 0 | 0.00% | 7.22% | 10.00% | 2 | certified (ESS 40); missed 3.3% of should-continue, bound 10.0% vs 10% |

**Whole chain:** silent-error bound 7.22% (within the 10.00% budget). Chain CERTIFIED.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| v0_baseline | true ≥0.50 / false ≥0.99 | 60/120 | 23 | 0 | 12.21% | 2 | no |
| v1_criteria | true ≥0.58 / false ≥0.76 | 80/120 | 37 | 0 | 7.78% | 1 | yes |
| v2_framing | true ≥0.69 / false ≥0.66 | 82/120 | 37 | 0 | 7.78% | 2 | yes |
| v3_choice16 | true ≥0.53 / false ≥0.97 | 77/120 | 37 | 0 | 7.78% | 2 | yes |
| v4_evidence | true ≥0.66 / false ≥0.62 | 82/120 | 39 | 0 | 7.39% | 2 | yes |
| vote(v1,v2,v3) ← chosen | true ≥0.50 / false ≥0.75 | 85/120 | 40 | 0 | 7.22% | 2 | yes |
| vote(v2,v4) | true ≥0.66 / false ≥0.64 | 82/120 | 38 | 0 | 7.58% | 2 | yes |

Error correlation between formulations (φ; near 1 means they fail on the same inputs, so voting between them buys little):

- v0_baseline / v1_criteria: 0.56
- v0_baseline / v2_framing: 0.34
- v0_baseline / v3_choice16: 0.73
- v0_baseline / v4_evidence: 0.03
- v0_baseline / vote(v1,v2,v3): 0.68
- v0_baseline / vote(v2,v4): 0.22
- v1_criteria / v2_framing: 0.72
- v1_criteria / v3_choice16: 0.78
- v1_criteria / v4_evidence: 0.33
- v1_criteria / vote(v1,v2,v3): 0.85
- v1_criteria / vote(v2,v4): 0.56
- v2_framing / v3_choice16: 0.51
- v2_framing / v4_evidence: 0.60
- v2_framing / vote(v1,v2,v3): 0.57
- v2_framing / vote(v2,v4): 0.86
- v3_choice16 / v4_evidence: 0.14
- v3_choice16 / vote(v1,v2,v3): 0.92
- v3_choice16 / vote(v2,v4): 0.36
- v4_evidence / vote(v1,v2,v3): 0.17
- v4_evidence / vote(v2,v4): 0.71
- vote(v1,v2,v3) / vote(v2,v4): 0.40

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


```json
{
  "error_budget": 0.1,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "vote(v1,v2,v3)",
      "gate": {
        "true": 0.5,
        "false": 0.75
      },
      "decided": 85,
      "n": 120,
      "errors": 0,
      "bound": 0.0721575245055146,
      "budget": 0.09999999999999998,
      "certified": true
    }
  }
}
```
