# Full invoice chain: compiled on Claude labels

Calibration: 119 docs from bal120 (36 invoices per labels). Held-out: 85 docs from chain_ver. Claude labels: 100 docs. Stop (miss) budget per step: 25%.

### Claude labeler agreement (independent second pass)

| field | agree | of |
|---|---|---|
| is_invoice | 20 | 20 |
| invoice_type | 20 | 20 |
| amount_consistent | 20 | 20 |
| total | 18 | 20 |
| approve | 19 | 20 |

## Chain budget 30%

### Calibration report

Chain error budget **30.00%** silent errors at 95% confidence, split over 5 neural step(s) (6.885% each). Symbolic steps are exact.

Silent errors are confident wrong answers within each step's budget scope; for steps budgeted on `continue`, that means wrong answers that let the chain continue, while confident wrong stops are counted separately as missed automation.

| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul (on continue) | c_text | true ≥0.90 / false ≥0.51 | 73/119 (61%) | 20 | 1 | 1.37% | 20.67% | 6.89% | 1 | UNCERTIFIED: needs ≥42 continued (accepted) decisions, 0 errors; missed 2.8% of should-continue, bound 12.5% vs 25% |
| invoice_type | neural · choice (on continue) | c_text | 0.820 | 11/20 (55%) | 11 | 0 | 0.00% | 23.84% | 6.89% | 0 | UNCERTIFIED: needs ≥42 continued (accepted) decisions, 0 errors; missed 0.0% of should-continue, bound 15.3% vs 25% |
| amount_consistent | neural · noul (on continue) | c_text | true ≥0.51 / false ≥0.51 | 11/11 (100%) | 6 | 0 | 0.00% | 39.30% | 6.89% | 4 | UNCERTIFIED: needs ≥42 continued (accepted) decisions, 0 errors; missed 40.0% of should-continue, bound 100.0% vs 25% |
| under_5000 | neural · noul (on continue) | c_atoms | true ≥0.51 / false ≥0.51 | 6/6 (100%) | 4 | 0 | 0.00% | 52.71% | 6.89% | 0 | UNCERTIFIED: needs ≥42 continued (accepted) decisions, 0 errors; missed 0.0% of should-continue, bound 52.7% vs 25% |
| payable | neural · noul (on continue) | c_atoms | true ≥0.69 / false ≥0.51 | 3/4 (75%) | 1 | 1 | 33.33% | 97.47% | 6.89% | 1 | UNCERTIFIED: needs ≥42 continued (accepted) decisions, 0 errors; missed 50.0% of should-continue, bound 97.5% vs 25% |
| decide | symbolic | exact rule | | | | 0 | 0 | 0 | 0 | | exact |

**Whole chain:** silent-error bound 99.56% (over the 30.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| c_text ← chosen | true ≥0.90 / false ≥0.51 | 73/119 | 20 | 1 | 20.67% | 1 | no |

## invoice_type: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| c_text ← chosen | 0.820 | 11/20 | 11 | 0 | 23.84% | 0 | no |

## amount_consistent: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| c_text ← chosen | true ≥0.51 / false ≥0.51 | 11/11 | 6 | 0 | 39.30% | 4 | no |

## under_5000: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| c_atoms ← chosen | true ≥0.51 / false ≥0.51 | 6/6 | 4 | 0 | 52.71% | 0 | no |

## payable: formulations tried

| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |
|---|---|---|---|---|---|---|---|
| c_atoms ← chosen | true ≥0.69 / false ≥0.51 | 3/4 | 1 | 1 | 97.47% | 1 | no |

Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` runs on held-out data.


### Per-step verification on held-out data

| step | formulation | gate τ | decided | silent errors | rate | 95% bound | budget | holds |
|---|---|---|---|---|---|---|---|---|
| is_invoice | c_text | true ≥0.90 / false ≥0.51 | 56/85 (66%) | 3 | 5.36% | 35.94% | 6.89% | NO |
| invoice_type | c_text | 0.820 | 10/16 (62%) | 0 | 0.00% | 25.89% | 6.89% | NO |
| amount_consistent | c_text | true ≥0.51 / false ≥0.51 | 10/10 (100%) | 0 | 0.00% | 31.23% | 6.89% | NO |
| under_5000 | c_atoms | true ≥0.51 / false ≥0.51 | 8/8 (100%) | 0 | 0.00% | 63.16% | 6.89% | NO |
| payable | c_atoms | true ≥0.69 / false ≥0.51 | 3/3 (100%) | 0 | 0.00% | 77.64% | 6.89% | NO |

**Whole chain on held-out data:** silent-error bound 97.31% vs budget 30.00%.


### End to end on held-out documents (Decision monad replay)

85 documents; 8 should be approved per Claude's labels.

| outcome | count | share |
|---|---|---|
| auto-approved, correct | 2 | 2% |
| **auto-approved, wrong (silent error)** | 0 | 0% |
| blocked for review (low confidence) | 38 | 45% |
| stopped, correct (not approvable) | 41 | 48% |
| stopped, wrong (approvable invoice rejected) | 4 | 5% |

Blocked at step: is_invoice 29, invoice_type 9


```json
{
  "error_budget": 0.3,
  "confidence": 0.95,
  "steps": {
    "is_invoice": {
      "formulation": "c_text",
      "gate": {
        "true": 0.9,
        "false": 0.51
      },
      "decided": 73,
      "n": 119,
      "errors": 1,
      "bound": 0.20672537900806995,
      "budget": 0.06885008490516231,
      "certified": false
    },
    "invoice_type": {
      "formulation": "c_text",
      "gate": {
        "*": 0.82
      },
      "decided": 11,
      "n": 20,
      "errors": 0,
      "bound": 0.2384041903808526,
      "budget": 0.06885008490516231,
      "certified": false
    },
    "amount_consistent": {
      "formulation": "c_text",
      "gate": {
        "true": 0.51,
        "false": 0.51
      },
      "decided": 11,
      "n": 11,
      "errors": 0,
      "bound": 0.39303776899708265,
      "budget": 0.06885008490516231,
      "certified": false
    },
    "under_5000": {
      "formulation": "c_atoms",
      "gate": {
        "true": 0.51,
        "false": 0.51
      },
      "decided": 6,
      "n": 6,
      "errors": 0,
      "bound": 0.527129195498412,
      "budget": 0.06885008490516231,
      "certified": false
    },
    "payable": {
      "formulation": "c_atoms",
      "gate": {
        "true": 0.69,
        "false": 0.51
      },
      "decided": 3,
      "n": 4,
      "errors": 1,
      "bound": 0.9746794344808964,
      "budget": 0.06885008490516231,
      "certified": false
    }
  }
}
```
