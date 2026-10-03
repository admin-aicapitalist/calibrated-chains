# Compiling `is_invoice` on bal120

120 labeled calibration docs (audited labels), 5 single formulations, 2 ensembles. Not available as text runs on bal120: v5_image_text, j_first70, j_last70, j_mid70, j_trim80, j_inverted, j_clerk.

## Budget 1%, one gate

### Report

Chain error budget **1.00%** silent errors at 95% confidence, split over 1 neural step(s) (1.000% each). Symbolic steps are exact.

| step | type | formulation | gate τ | decided | silent errors | rate | 95% bound | budget | status |
|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul | v4_evidence | 0.745 | 72/120 (60%) | 0 | 0.00% | 4.08% | 1.00% | UNCERTIFIED: needs ≥299 decided, 0 errors |

**Whole chain:** silent-error bound 4.08% (over the 1.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | silent errors | 95% bound | fits budget |
|---|---|---|---|---|---|
| v0_baseline | 0.990 | 37/120 | 2 | 16.05% | no |
| v1_criteria | 0.835 | 64/120 | 0 | 4.57% | no |
| v2_framing | 0.820 | 62/120 | 0 | 4.72% | no |
| v3_choice16 | 0.995 | 29/120 | 0 | 9.81% | no |
| v4_evidence ← chosen | 0.745 | 72/120 | 0 | 4.08% | no |
| vote(v1,v2,v3) | 0.885 | 57/120 | 0 | 5.12% | no |
| vote(v2,v4) | 0.785 | 66/120 | 0 | 4.44% | no |

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
        "*": 0.745
      },
      "decided": 72,
      "n": 120,
      "errors": 0,
      "bound": 0.04075368623063991,
      "budget": 0.010000000000000009,
      "certified": false
    }
  }
}
```

## Budget 1%, separate yes/no gates

### Report

Chain error budget **1.00%** silent errors at 95% confidence, split over 1 neural step(s) (1.000% each). Symbolic steps are exact.

| step | type | formulation | gate τ | decided | silent errors | rate | 95% bound | budget | status |
|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul | v4_evidence | true ≥0.66 / false ≥0.75 | 76/120 (63%) | 0 | 0.00% | 3.87% | 1.00% | UNCERTIFIED: needs ≥299 decided, 0 errors |

**Whole chain:** silent-error bound 3.87% (over the 1.00% budget). Chain NOT certified.

## is_invoice: formulations tried

| formulation | gate τ | decided | silent errors | 95% bound | fits budget |
|---|---|---|---|---|---|
| v0_baseline | true ≥0.50 / false ≥0.99 | 60/120 | 2 | 10.12% | no |
| v1_criteria | true ≥0.57 / false ≥0.84 | 74/120 | 0 | 3.97% | no |
| v2_framing | true ≥0.67 / false ≥0.82 | 70/120 | 0 | 4.19% | no |
| v3_choice16 | true ≥0.50 / false ≥0.99 | 70/120 | 1 | 6.60% | no |
| v4_evidence ← chosen | true ≥0.66 / false ≥0.75 | 76/120 | 0 | 3.87% | no |
| vote(v1,v2,v3) | true ≥0.50 / false ≥0.89 | 72/120 | 0 | 4.08% | no |
| vote(v2,v4) | true ≥0.66 / false ≥0.79 | 73/120 | 0 | 4.02% | no |

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
        "true": 0.66,
        "false": 0.75
      },
      "decided": 76,
      "n": 120,
      "errors": 0,
      "bound": 0.03865076672572554,
      "budget": 0.010000000000000009,
      "certified": false
    }
  }
}
```

## Budget 5%, one gate

### Report

Chain error budget **5.00%** silent errors at 95% confidence, split over 1 neural step(s) (5.000% each). Symbolic steps are exact.

| step | type | formulation | gate τ | decided | silent errors | rate | 95% bound | budget | status |
|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul | v4_evidence | 0.750 | 72/120 (60%) | 0 | 0.00% | 4.08% | 5.00% | certified |

**Whole chain:** silent-error bound 4.08% (within the 5.00% budget). Chain CERTIFIED.

## is_invoice: formulations tried

| formulation | gate τ | decided | silent errors | 95% bound | fits budget |
|---|---|---|---|---|---|
| v0_baseline | 0.990 | 37/120 | 2 | 16.05% | no |
| v1_criteria | 0.845 | 64/120 | 0 | 4.57% | yes |
| v2_framing | 0.845 | 62/120 | 0 | 4.72% | yes |
| v3_choice16 | 0.995 | 29/120 | 0 | 9.81% | no |
| v4_evidence ← chosen | 0.750 | 72/120 | 0 | 4.08% | yes |
| vote(v1,v2,v3) | 0.885 | 57/120 | 0 | 5.12% | no |
| vote(v2,v4) | 0.800 | 66/120 | 0 | 4.44% | yes |

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
        "*": 0.75
      },
      "decided": 72,
      "n": 120,
      "errors": 0,
      "bound": 0.04075368623063991,
      "budget": 0.050000000000000044,
      "certified": true
    }
  }
}
```

## Budget 5%, separate yes/no gates

### Report

Chain error budget **5.00%** silent errors at 95% confidence, split over 1 neural step(s) (5.000% each). Symbolic steps are exact.

| step | type | formulation | gate τ | decided | silent errors | rate | 95% bound | budget | status |
|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul | v4_evidence | true ≥0.66 / false ≥0.75 | 76/120 (63%) | 0 | 0.00% | 3.87% | 5.00% | certified |

**Whole chain:** silent-error bound 3.87% (within the 5.00% budget). Chain CERTIFIED.

## is_invoice: formulations tried

| formulation | gate τ | decided | silent errors | 95% bound | fits budget |
|---|---|---|---|---|---|
| v0_baseline | true ≥0.50 / false ≥0.99 | 60/120 | 2 | 10.12% | no |
| v1_criteria | true ≥0.58 / false ≥0.84 | 74/120 | 0 | 3.97% | yes |
| v2_framing | true ≥0.69 / false ≥0.84 | 70/120 | 0 | 4.19% | yes |
| v3_choice16 | true ≥0.50 / false ≥0.99 | 70/120 | 1 | 6.60% | no |
| v4_evidence ← chosen | true ≥0.66 / false ≥0.75 | 76/120 | 0 | 3.87% | yes |
| vote(v1,v2,v3) | true ≥0.50 / false ≥0.91 | 72/120 | 0 | 4.08% | yes |
| vote(v2,v4) | true ≥0.66 / false ≥0.80 | 73/120 | 0 | 4.02% | yes |

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
        "true": 0.66,
        "false": 0.75
      },
      "decided": 76,
      "n": 120,
      "errors": 0,
      "bound": 0.03865076672572554,
      "budget": 0.050000000000000044,
      "certified": true
    }
  }
}
```

## Budget 10%, one gate

### Report

Chain error budget **10.00%** silent errors at 95% confidence, split over 1 neural step(s) (10.000% each). Symbolic steps are exact.

| step | type | formulation | gate τ | decided | silent errors | rate | 95% bound | budget | status |
|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul | v2_framing | 0.615 | 90/120 (75%) | 4 | 4.44% | 9.88% | 10.00% | certified |

**Whole chain:** silent-error bound 9.88% (within the 10.00% budget). Chain CERTIFIED.

## is_invoice: formulations tried

| formulation | gate τ | decided | silent errors | 95% bound | fits budget |
|---|---|---|---|---|---|
| v0_baseline | 0.990 | 37/120 | 2 | 16.05% | no |
| v1_criteria | 0.740 | 77/120 | 3 | 9.76% | yes |
| v2_framing ← chosen | 0.615 | 90/120 | 4 | 9.88% | yes |
| v3_choice16 | 0.995 | 29/120 | 0 | 9.81% | yes |
| v4_evidence | 0.655 | 81/120 | 2 | 7.57% | yes |
| vote(v1,v2,v3) | 0.735 | 79/120 | 3 | 9.52% | yes |
| vote(v2,v4) | 0.635 | 85/120 | 3 | 8.87% | yes |

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
      "formulation": "v2_framing",
      "gate": {
        "*": 0.615
      },
      "decided": 90,
      "n": 120,
      "errors": 4,
      "bound": 0.09882084611586987,
      "budget": 0.09999999999999998,
      "certified": true
    }
  }
}
```

## Budget 10%, separate yes/no gates

### Report

Chain error budget **10.00%** silent errors at 95% confidence, split over 1 neural step(s) (10.000% each). Symbolic steps are exact.

| step | type | formulation | gate τ | decided | silent errors | rate | 95% bound | budget | status |
|---|---|---|---|---|---|---|---|---|---|
| is_invoice | neural · noul | v2_framing | true ≥0.62 / false ≥0.58 | 94/120 (78%) | 4 | 4.26% | 9.47% | 10.00% | certified |

**Whole chain:** silent-error bound 9.47% (within the 10.00% budget). Chain CERTIFIED.

## is_invoice: formulations tried

| formulation | gate τ | decided | silent errors | 95% bound | fits budget |
|---|---|---|---|---|---|
| v0_baseline | true ≥0.50 / false ≥0.99 | 60/120 | 2 | 10.12% | no |
| v1_criteria | true ≥0.50 / false ≥0.76 | 88/120 | 3 | 8.58% | yes |
| v2_framing ← chosen | true ≥0.62 / false ≥0.58 | 94/120 | 4 | 9.47% | yes |
| v3_choice16 | true ≥0.53 / false ≥0.96 | 81/120 | 3 | 9.29% | yes |
| v4_evidence | true ≥0.66 / false ≥0.51 | 92/120 | 4 | 9.67% | yes |
| vote(v1,v2,v3) | true ≥0.50 / false ≥0.72 | 89/120 | 4 | 9.99% | yes |
| vote(v2,v4) | true ≥0.66 / false ≥0.53 | 93/120 | 4 | 9.57% | yes |

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
      "formulation": "v2_framing",
      "gate": {
        "true": 0.62,
        "false": 0.58
      },
      "decided": 94,
      "n": 120,
      "errors": 4,
      "bound": 0.09473220589715114,
      "budget": 0.09999999999999998,
      "certified": true
    }
  }
}
```
