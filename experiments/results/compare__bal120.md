## Variants on bal120

- **@0.9**: at τ=0.9, invoices accepted / false invoices passed / invoices confidently rejected.
- **safe τ**: lowest τ with ≤1% silent errors on this sample (in-sample pick), and invoices auto-accepted / false invoices at that τ.

| variant | recall | precision | AUROC | ECE | @0.9 acc/false/missed | safe τ | safe acc/false |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.367 | 0.957 | 0.921 | 0.276 | 11 / 1 / 23 | 0.995 | 0 / 0 |
| v0_baseline + platt(CV) | 0.750 | 0.900 | 0.920 | 0.065 | 29 / 1 / 0 | 1.000 | 0 / 0 |
| v1_criteria | 0.700 | 0.933 | 0.934 | 0.084 | 21 / 1 / 0 | 0.965 | 6 / 0 |
| v1_criteria + platt(CV) | 0.867 | 0.825 | 0.924 | 0.071 | 29 / 1 / 0 | 1.000 | 0 / 0 |
| v2_framing | 0.800 | 0.889 | 0.939 | 0.091 | 22 / 1 / 0 | 0.960 | 8 / 0 |
| v2_framing + platt(CV) | 0.883 | 0.869 | 0.936 | 0.063 | 30 / 1 / 0 | 1.000 | 0 / 0 |
| v3_choice16 | 0.600 | 0.973 | 0.922 | 0.155 | 19 / 1 / 10 | 0.995 | 0 / 0 |
| v3_choice16 + platt(CV) | 0.783 | 0.839 | 0.918 | 0.068 | 35 / 1 / 0 | 0.990 | 1 / 0 |
| v4_evidence | 0.917 | 0.846 | 0.940 | 0.104 | 22 / 1 / 0 | 0.960 | 4 / 0 |
| v4_evidence + platt(CV) | 0.917 | 0.846 | 0.936 | 0.095 | 31 / 1 / 0 | 1.000 | 0 / 0 |
| v5_image_text | (running: 5/120) |||||||
