# v0_baseline on dev10

### Raw Clef probabilities

n=205 (invoices 13) | acc 0.951 | P 0.800 R 0.308 F1 0.444 | AUROC 0.965 | AP 0.637 | Brier 0.041 | NLL 0.146 | ECE 0.030

Reliability (p_invoice bin -> observed invoice rate):

| bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 194 | 0.013 | 0.026 |
| 0.1-0.2 | 5 | 0.145 | 0.600 |
| 0.2-0.3 | 1 | 0.230 | 1.000 |
| 0.8-0.9 | 1 | 0.899 | 1.000 |
| 0.9-1.0 | 4 | 0.955 | 0.750 |

Gate (pass iff confidence >= tau):

| tau | coverage | selective acc | silent errors | false invoice | missed invoice | invoices accepted | blocked |
|---|---|---|---|---|---|---|---|
| 0.6 | 1.000 | 0.951 | 10 | 1 | 9 | 4 | 0 |
| 0.7 | 1.000 | 0.951 | 10 | 1 | 9 | 4 | 0 |
| 0.8 | 0.995 | 0.956 | 9 | 1 | 8 | 4 | 1 |
| 0.9 | 0.966 | 0.970 | 6 | 1 | 5 | 3 | 7 |
| 0.95 | 0.927 | 0.974 | 5 | 1 | 4 | 2 | 15 |
| 0.99 | 0.615 | 1.000 | 0 | 0 | 0 | 0 | 79 |

False-positive classes (non-invoice with p>=0.5): budget 1
- validation/539 (invoice): p_invoice=0.016
- validation/1277 (budget): p_invoice=0.970
- validation/1448 (invoice): p_invoice=0.033
- validation/508 (invoice): p_invoice=0.036
- validation/1815 (invoice): p_invoice=0.044
- validation/493 (invoice): p_invoice=0.079
- validation/83 (invoice): p_invoice=0.125
- validation/863 (invoice): p_invoice=0.155

## Strategies, gate tuned for <= 1% silent errors

Each row's tau is the lowest that keeps silent errors <= 1% of passed decisions *on this same sample*; it's an optimistic in-sample pick, and only the test run checks it.

| strategy | acc | AUROC | Brier | ECE | tau | coverage | silent errors | invoices auto-accepted |
|---|---|---|---|---|---|---|---|---|
| raw | 0.951 | 0.965 | 0.041 | 0.030 | 0.970 | 0.854 | 1 | 0/13 |
| platt (5-fold CV) | 0.956 | 0.956 | 0.034 | 0.023 | 0.975 | 0.659 | 1 | 4/13 |
