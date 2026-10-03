# v0_baseline on dev

### Raw Clef probabilities

n=426 (invoices 126) | acc 0.808 | P 0.978 R 0.357 F1 0.523 | AUROC 0.927 | AP 0.853 | Brier 0.165 | NLL 0.612 | ECE 0.162

Reliability (p_invoice bin -> observed invoice rate):

| bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 349 | 0.015 | 0.152 |
| 0.1-0.2 | 16 | 0.144 | 0.875 |
| 0.2-0.3 | 8 | 0.222 | 1.000 |
| 0.3-0.4 | 6 | 0.334 | 0.833 |
| 0.4-0.5 | 1 | 0.469 | 1.000 |
| 0.5-0.6 | 4 | 0.553 | 1.000 |
| 0.6-0.7 | 1 | 0.680 | 1.000 |
| 0.7-0.8 | 7 | 0.747 | 1.000 |
| 0.8-0.9 | 8 | 0.857 | 1.000 |
| 0.9-1.0 | 26 | 0.953 | 0.962 |

Gate (pass iff confidence >= tau):

| tau | coverage | selective acc | silent errors | false invoice | missed invoice | invoices accepted | blocked |
|---|---|---|---|---|---|---|---|
| 0.6 | 0.988 | 0.808 | 81 | 1 | 80 | 41 | 5 |
| 0.7 | 0.972 | 0.816 | 76 | 1 | 75 | 40 | 12 |
| 0.8 | 0.937 | 0.830 | 68 | 1 | 67 | 33 | 27 |
| 0.9 | 0.880 | 0.856 | 54 | 1 | 53 | 25 | 51 |
| 0.95 | 0.824 | 0.866 | 47 | 1 | 46 | 16 | 75 |
| 0.99 | 0.477 | 0.970 | 6 | 0 | 6 | 0 | 223 |

False-positive classes (non-invoice with p>=0.5): budget 1
- validation/1024 (invoice): p_invoice=0.007
- validation/1857 (invoice): p_invoice=0.007
- validation/759 (invoice): p_invoice=0.007
- validation/363 (invoice): p_invoice=0.008
- validation/1817 (invoice): p_invoice=0.009
- validation/338 (invoice): p_invoice=0.009
- validation/1588 (invoice): p_invoice=0.010
- validation/1394 (invoice): p_invoice=0.012

## Strategies, gate tuned for <= 1% silent errors

Each row's tau is the lowest that keeps silent errors <= 1% of passed decisions *on this same sample*; it's an optimistic in-sample pick, and only the test run checks it.

| strategy | acc | AUROC | Brier | ECE | tau | coverage | silent errors | invoices auto-accepted |
|---|---|---|---|---|---|---|---|---|
| raw | 0.808 | 0.927 | 0.165 | 0.162 | 0.995 | 0.070 | 0 | 0/126 |
| platt (5-fold CV) | 0.864 | 0.923 | 0.098 | 0.043 | 0.940 | 0.329 | 1 | 51/126 |
