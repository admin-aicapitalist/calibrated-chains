## Variants on bal120 (audited labels, see label_noise.md)

- **@0.9**: at τ=0.9, invoices accepted / false invoices passed / invoices confidently rejected.
- **safe τ**: lowest τ with ≤1% silent errors on this sample (in-sample pick), and invoices auto-accepted / false invoices at that τ.

| variant | recall | precision | AUROC | ECE | @0.9 acc/false/missed | safe τ | safe acc/false |
|---|---|---|---|---|---|---|---|
| v0_baseline | 0.377 | 1.000 | 0.937 | 0.268 | 12 / 0 / 23 | 0.995 | 0 / 0 |
| v0_baseline + platt(CV) | 0.820 | 0.893 | 0.935 | 0.060 | 40 / 1 / 0 | 0.920 | 39 / 0 |
| v1_criteria | 0.705 | 0.956 | 0.949 | 0.093 | 22 / 0 / 0 | 0.835 | 27 / 0 |
| v1_criteria + platt(CV) | 0.869 | 0.841 | 0.942 | 0.060 | 33 / 0 / 1 | 0.930 | 33 / 0 |
| v2_framing | 0.803 | 0.907 | 0.954 | 0.097 | 23 / 0 / 0 | 0.820 | 29 / 0 |
| v2_framing + platt(CV) | 0.918 | 0.875 | 0.951 | 0.088 | 37 / 0 / 2 | 0.945 | 33 / 0 |
| v3_choice16 | 0.607 | 1.000 | 0.937 | 0.147 | 20 / 0 / 10 | 0.995 | 0 / 0 |
| v3_choice16 + platt(CV) | 0.836 | 0.836 | 0.934 | 0.082 | 36 / 0 / 2 | 0.925 | 36 / 0 |
| v4_evidence | (running: 0/120) |||||||
