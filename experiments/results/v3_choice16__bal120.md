# v3_choice16 on bal120

### Raw Clef probabilities

n=120 (invoices 60) | acc 0.792 | P 0.973 R 0.600 F1 0.742 | AUROC 0.922 | AP 0.912 | Brier 0.166 | NLL 0.548 | ECE 0.155

Reliability (p_invoice bin -> observed invoice rate):

| bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 59 | 0.024 | 0.169 |
| 0.1-0.2 | 11 | 0.121 | 0.636 |
| 0.2-0.3 | 8 | 0.241 | 0.375 |
| 0.3-0.4 | 1 | 0.352 | 1.000 |
| 0.4-0.5 | 4 | 0.421 | 0.750 |
| 0.5-0.6 | 1 | 0.533 | 1.000 |
| 0.6-0.7 | 1 | 0.650 | 1.000 |
| 0.7-0.8 | 8 | 0.751 | 1.000 |
| 0.8-0.9 | 7 | 0.843 | 1.000 |
| 0.9-1.0 | 20 | 0.946 | 0.950 |

Gate (pass iff confidence >= tau):

| tau | coverage | selective acc | silent errors | false invoice | missed invoice | invoices accepted | blocked |
|---|---|---|---|---|---|---|---|
| 0.6 | 0.958 | 0.809 | 22 | 1 | 21 | 35 | 5 |
| 0.7 | 0.942 | 0.814 | 21 | 1 | 20 | 34 | 7 |
| 0.8 | 0.808 | 0.814 | 18 | 1 | 17 | 26 | 23 |
| 0.9 | 0.658 | 0.861 | 11 | 1 | 10 | 19 | 41 |
| 0.95 | 0.483 | 0.914 | 5 | 1 | 4 | 11 | 62 |
| 0.99 | 0.275 | 0.970 | 1 | 0 | 1 | 0 | 87 |

False-positive classes (non-invoice with p>=0.5): budget 1
- validation/1588 (invoice): p_invoice=0.009
- validation/1115 (invoice): p_invoice=0.010
- validation/508 (invoice): p_invoice=0.038
- validation/338 (invoice): p_invoice=0.041
- validation/1277 (budget): p_invoice=0.953
- validation/1642 (invoice): p_invoice=0.055
- validation/1394 (invoice): p_invoice=0.064
- validation/1091 (invoice): p_invoice=0.070

## Strategies, gate tuned for <= 1% silent errors

Each row's tau is the lowest that keeps silent errors <= 1% of passed decisions *on this same sample*; it's an optimistic in-sample pick, and only the test run checks it.

| strategy | acc | AUROC | Brier | ECE | tau | coverage | silent errors | invoices auto-accepted |
|---|---|---|---|---|---|---|---|---|
| raw | 0.792 | 0.922 | 0.166 | 0.155 | 0.995 | 0.242 | 0 | 0/60 |
| platt (5-fold CV) | 0.817 | 0.918 | 0.113 | 0.068 | 0.990 | 0.008 | 0 | 1/60 |
