# v2_framing on bal120

### Raw Clef probabilities

n=120 (invoices 60) | acc 0.850 | P 0.889 R 0.800 F1 0.842 | AUROC 0.939 | AP 0.925 | Brier 0.107 | NLL 0.348 | ECE 0.091

Reliability (p_invoice bin -> observed invoice rate):

| bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 25 | 0.055 | 0.000 |
| 0.1-0.2 | 11 | 0.145 | 0.091 |
| 0.2-0.3 | 5 | 0.222 | 0.200 |
| 0.3-0.4 | 10 | 0.353 | 0.100 |
| 0.4-0.5 | 15 | 0.450 | 0.600 |
| 0.5-0.6 | 12 | 0.543 | 0.750 |
| 0.6-0.7 | 6 | 0.643 | 0.667 |
| 0.7-0.8 | 6 | 0.745 | 1.000 |
| 0.8-0.9 | 7 | 0.862 | 1.000 |
| 0.9-1.0 | 23 | 0.950 | 0.957 |

Gate (pass iff confidence >= tau):

| tau | coverage | selective acc | silent errors | false invoice | missed invoice | invoices accepted | blocked |
|---|---|---|---|---|---|---|---|
| 0.6 | 0.775 | 0.935 | 6 | 3 | 3 | 39 | 27 |
| 0.7 | 0.642 | 0.961 | 3 | 1 | 2 | 35 | 43 |
| 0.8 | 0.550 | 0.970 | 2 | 1 | 1 | 29 | 54 |
| 0.9 | 0.400 | 0.979 | 1 | 1 | 0 | 22 | 72 |
| 0.95 | 0.192 | 0.957 | 1 | 1 | 0 | 12 | 97 |
| 0.99 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 120 |

False-positive classes (non-invoice with p>=0.5): budget 1, email 1, handwritten 2, news article 1, specification 1
- validation/1277 (budget): p_invoice=0.956
- validation/1588 (invoice): p_invoice=0.182
- validation/1115 (invoice): p_invoice=0.226
- validation/1922 (specification): p_invoice=0.661
- validation/1546 (invoice): p_invoice=0.355
- validation/1926 (news article): p_invoice=0.614
- validation/1840 (handwritten): p_invoice=0.587
- validation/1900 (handwritten): p_invoice=0.583

## Strategies, gate tuned for <= 1% silent errors

Each row's tau is the lowest that keeps silent errors <= 1% of passed decisions *on this same sample*; it's an optimistic in-sample pick, and only the test run checks it.

| strategy | acc | AUROC | Brier | ECE | tau | coverage | silent errors | invoices auto-accepted |
|---|---|---|---|---|---|---|---|---|
| raw | 0.850 | 0.939 | 0.107 | 0.091 | 0.960 | 0.117 | 0 | 8/60 |
| platt (5-fold CV) | 0.875 | 0.936 | 0.099 | 0.063 | 1.000 | 0.000 | 0 | 0/60 |
