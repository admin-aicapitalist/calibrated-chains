# v1_criteria on bal120

### Raw Clef probabilities

n=120 (invoices 60) | acc 0.825 | P 0.933 R 0.700 F1 0.800 | AUROC 0.934 | AP 0.921 | Brier 0.116 | NLL 0.363 | ECE 0.084

Reliability (p_invoice bin -> observed invoice rate):

| bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 28 | 0.051 | 0.000 |
| 0.1-0.2 | 12 | 0.135 | 0.083 |
| 0.2-0.3 | 8 | 0.253 | 0.500 |
| 0.3-0.4 | 12 | 0.357 | 0.417 |
| 0.4-0.5 | 15 | 0.449 | 0.533 |
| 0.5-0.6 | 11 | 0.547 | 0.818 |
| 0.6-0.7 | 1 | 0.617 | 1.000 |
| 0.7-0.8 | 6 | 0.744 | 1.000 |
| 0.8-0.9 | 5 | 0.878 | 1.000 |
| 0.9-1.0 | 22 | 0.952 | 0.955 |

Gate (pass iff confidence >= tau):

| tau | coverage | selective acc | silent errors | false invoice | missed invoice | invoices accepted | blocked |
|---|---|---|---|---|---|---|---|
| 0.6 | 0.783 | 0.883 | 11 | 1 | 10 | 33 | 26 |
| 0.7 | 0.675 | 0.926 | 6 | 1 | 5 | 32 | 39 |
| 0.8 | 0.558 | 0.970 | 2 | 1 | 1 | 26 | 53 |
| 0.9 | 0.417 | 0.980 | 1 | 1 | 0 | 21 | 70 |
| 0.95 | 0.258 | 0.968 | 1 | 1 | 0 | 15 | 89 |
| 0.99 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 120 |

False-positive classes (non-invoice with p>=0.5): budget 1, news article 1, specification 1
- validation/1277 (budget): p_invoice=0.962
- validation/1588 (invoice): p_invoice=0.166
- validation/1115 (invoice): p_invoice=0.251
- validation/338 (invoice): p_invoice=0.258
- validation/1546 (invoice): p_invoice=0.282
- validation/363 (invoice): p_invoice=0.293
- validation/1394 (invoice): p_invoice=0.351
- validation/366 (invoice): p_invoice=0.361

## Strategies, gate tuned for <= 1% silent errors

Each row's tau is the lowest that keeps silent errors <= 1% of passed decisions *on this same sample*; it's an optimistic in-sample pick, and only the test run checks it.

| strategy | acc | AUROC | Brier | ECE | tau | coverage | silent errors | invoices auto-accepted |
|---|---|---|---|---|---|---|---|---|
| raw | 0.825 | 0.934 | 0.116 | 0.084 | 0.965 | 0.083 | 0 | 6/60 |
| platt (5-fold CV) | 0.842 | 0.924 | 0.107 | 0.071 | 1.000 | 0.000 | 0 | 0/60 |
