# v0_baseline on bal120

### Raw Clef probabilities

n=120 (invoices 60) | acc 0.675 | P 0.957 R 0.367 F1 0.530 | AUROC 0.921 | AP 0.895 | Brier 0.273 | NLL 0.985 | ECE 0.276

Reliability (p_invoice bin -> observed invoice rate):

| bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 82 | 0.018 | 0.280 |
| 0.1-0.2 | 7 | 0.144 | 1.000 |
| 0.2-0.3 | 4 | 0.217 | 1.000 |
| 0.3-0.4 | 3 | 0.334 | 1.000 |
| 0.4-0.5 | 1 | 0.469 | 1.000 |
| 0.5-0.6 | 3 | 0.551 | 1.000 |
| 0.7-0.8 | 3 | 0.756 | 1.000 |
| 0.8-0.9 | 5 | 0.880 | 1.000 |
| 0.9-1.0 | 12 | 0.948 | 0.917 |

Gate (pass iff confidence >= tau):

| tau | coverage | selective acc | silent errors | false invoice | missed invoice | invoices accepted | blocked |
|---|---|---|---|---|---|---|---|
| 0.6 | 0.967 | 0.672 | 38 | 1 | 37 | 19 | 4 |
| 0.7 | 0.942 | 0.690 | 35 | 1 | 34 | 19 | 7 |
| 0.8 | 0.883 | 0.708 | 31 | 1 | 30 | 16 | 14 |
| 0.9 | 0.783 | 0.745 | 24 | 1 | 23 | 11 | 26 |
| 0.95 | 0.692 | 0.735 | 22 | 1 | 21 | 5 | 37 |
| 0.99 | 0.308 | 0.946 | 2 | 0 | 2 | 0 | 83 |

False-positive classes (non-invoice with p>=0.5): budget 1
- validation/363 (invoice): p_invoice=0.008
- validation/338 (invoice): p_invoice=0.009
- validation/1588 (invoice): p_invoice=0.010
- validation/1394 (invoice): p_invoice=0.012
- validation/1500 (invoice): p_invoice=0.012
- validation/2000 (invoice): p_invoice=0.013
- validation/1115 (invoice): p_invoice=0.014
- validation/1021 (invoice): p_invoice=0.014

## Strategies, gate tuned for <= 1% silent errors

Each row's tau is the lowest that keeps silent errors <= 1% of passed decisions *on this same sample*; it's an optimistic in-sample pick, and only the test run checks it.

| strategy | acc | AUROC | Brier | ECE | tau | coverage | silent errors | invoices auto-accepted |
|---|---|---|---|---|---|---|---|---|
| raw | 0.675 | 0.921 | 0.273 | 0.276 | 0.995 | 0.042 | 0 | 0/60 |
| platt (5-fold CV) | 0.833 | 0.920 | 0.116 | 0.065 | 1.000 | 0.000 | 0 | 0/60 |
