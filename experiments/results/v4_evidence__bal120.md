# v4_evidence on bal120

### Raw Clef probabilities

n=120 (invoices 60) | acc 0.875 | P 0.846 R 0.917 F1 0.880 | AUROC 0.940 | AP 0.923 | Brier 0.104 | NLL 0.341 | ECE 0.104

Reliability (p_invoice bin -> observed invoice rate):

| bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 24 | 0.048 | 0.000 |
| 0.1-0.2 | 10 | 0.137 | 0.000 |
| 0.2-0.3 | 7 | 0.257 | 0.286 |
| 0.3-0.4 | 5 | 0.381 | 0.200 |
| 0.4-0.5 | 9 | 0.461 | 0.222 |
| 0.5-0.6 | 16 | 0.539 | 0.750 |
| 0.6-0.7 | 12 | 0.635 | 0.583 |
| 0.7-0.8 | 6 | 0.762 | 1.000 |
| 0.8-0.9 | 8 | 0.851 | 1.000 |
| 0.9-1.0 | 23 | 0.945 | 0.957 |

Gate (pass iff confidence >= tau):

| tau | coverage | selective acc | silent errors | false invoice | missed invoice | invoices accepted | blocked |
|---|---|---|---|---|---|---|---|
| 0.6 | 0.792 | 0.905 | 9 | 6 | 3 | 43 | 25 |
| 0.7 | 0.650 | 0.962 | 3 | 1 | 2 | 36 | 42 |
| 0.8 | 0.542 | 0.985 | 1 | 1 | 0 | 30 | 55 |
| 0.9 | 0.392 | 0.979 | 1 | 1 | 0 | 22 | 73 |
| 0.95 | 0.208 | 0.960 | 1 | 1 | 0 | 10 | 95 |
| 0.99 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 120 |

False-positive classes (non-invoice with p>=0.5): budget 1, email 1, file folder 2, handwritten 2, news article 1, presentation 1, scientific report 1, specification 1
- validation/1277 (budget): p_invoice=0.956
- validation/1588 (invoice): p_invoice=0.257
- validation/1115 (invoice): p_invoice=0.293
- validation/1922 (specification): p_invoice=0.653
- validation/1926 (news article): p_invoice=0.651
- validation/1900 (handwritten): p_invoice=0.637
- validation/1840 (handwritten): p_invoice=0.629
- validation/1546 (invoice): p_invoice=0.381

## Strategies, gate tuned for <= 1% silent errors

Each row's tau is the lowest that keeps silent errors <= 1% of passed decisions *on this same sample*; it's an optimistic in-sample pick, and only the test run checks it.

| strategy | acc | AUROC | Brier | ECE | tau | coverage | silent errors | invoices auto-accepted |
|---|---|---|---|---|---|---|---|---|
| raw | 0.875 | 0.940 | 0.104 | 0.104 | 0.960 | 0.100 | 0 | 4/60 |
| platt (5-fold CV) | 0.875 | 0.936 | 0.098 | 0.095 | 1.000 | 0.000 | 0 | 0/60 |
| doc_type=invoice only | 0.775 | 0.938 | 0.192 | 0.175 | 0.995 | 0.292 | 0 | 0/60 |
| mean(is_invoice, doc_type) | 0.800 | 0.945 | 0.128 | 0.098 | 0.930 | 0.333 | 0 | 10/60 |
| agree: min if both yes, max if both no | 0.875 | 0.939 | 0.124 | 0.155 | 0.900 | 0.300 | 0 | 12/60 |
| stacked logreg over 7 answers (5-fold CV) | 0.867 | 0.924 | 0.108 | 0.110 | 1.000 | 0.000 | 0 | 0/60 |
