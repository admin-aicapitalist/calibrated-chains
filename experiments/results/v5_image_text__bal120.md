# v5_image_text on bal120

### Raw Clef probabilities

n=120 (invoices 60) | acc 0.917 | P 0.981 R 0.850 F1 0.911 | AUROC 0.978 | AP 0.961 | Brier 0.069 | NLL 0.234 | ECE 0.073

Reliability (p_invoice bin -> observed invoice rate):

| bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 45 | 0.038 | 0.000 |
| 0.1-0.2 | 9 | 0.139 | 0.111 |
| 0.2-0.3 | 8 | 0.243 | 0.625 |
| 0.3-0.4 | 5 | 0.344 | 0.400 |
| 0.4-0.5 | 1 | 0.482 | 1.000 |
| 0.5-0.6 | 6 | 0.561 | 1.000 |
| 0.6-0.7 | 2 | 0.648 | 1.000 |
| 0.7-0.8 | 5 | 0.755 | 1.000 |
| 0.8-0.9 | 3 | 0.832 | 1.000 |
| 0.9-1.0 | 36 | 0.945 | 0.972 |

Gate (pass iff confidence >= tau):

| tau | coverage | selective acc | silent errors | false invoice | missed invoice | invoices accepted | blocked |
|---|---|---|---|---|---|---|---|
| 0.6 | 0.942 | 0.920 | 9 | 1 | 8 | 45 | 7 |
| 0.7 | 0.883 | 0.934 | 7 | 1 | 6 | 43 | 14 |
| 0.8 | 0.775 | 0.978 | 2 | 1 | 1 | 38 | 27 |
| 0.9 | 0.675 | 0.988 | 1 | 1 | 0 | 35 | 39 |
| 0.95 | 0.442 | 0.981 | 1 | 1 | 0 | 16 | 67 |
| 0.99 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 120 |

False-positive classes (non-invoice with p>=0.5): budget 1
- validation/1277 (budget): p_invoice=0.955
- validation/1115 (invoice): p_invoice=0.133
- validation/78 (invoice): p_invoice=0.224
- validation/1546 (invoice): p_invoice=0.247
- validation/842 (invoice): p_invoice=0.264
- validation/1448 (invoice): p_invoice=0.267
- validation/1588 (invoice): p_invoice=0.277
- validation/36 (invoice): p_invoice=0.336

## Strategies, gate tuned for <= 1% silent errors

Each row's tau is the lowest that keeps silent errors <= 1% of passed decisions *on this same sample*; it's an optimistic in-sample pick, and only the test run checks it.

| strategy | acc | AUROC | Brier | ECE | tau | coverage | silent errors | invoices auto-accepted |
|---|---|---|---|---|---|---|---|---|
| raw | 0.917 | 0.978 | 0.069 | 0.073 | 0.955 | 0.333 | 0 | 8/60 |
| platt (5-fold CV) | 0.925 | 0.974 | 0.049 | 0.052 | 1.000 | 0.000 | 0 | 0/60 |
| doc_type=invoice only | 0.833 | 0.974 | 0.129 | 0.125 | 1.000 | 0.000 | 0 | 0/60 |
| mean(is_invoice, doc_type) | 0.858 | 0.976 | 0.094 | 0.093 | 0.950 | 0.375 | 0 | 1/60 |
| agree: min if both yes, max if both no | 0.917 | 0.976 | 0.082 | 0.106 | 0.945 | 0.325 | 0 | 3/60 |
| stacked logreg over 7 answers (5-fold CV) | 0.900 | 0.959 | 0.068 | 0.059 | 1.000 | 0.000 | 0 | 0/60 |
