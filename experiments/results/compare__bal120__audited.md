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
| v4_evidence | 0.918 | 0.862 | 0.955 | 0.112 | 23 / 0 / 0 | 0.745 | 35 / 0 |
| v4_evidence + platt(CV) | 0.918 | 0.848 | 0.952 | 0.079 | 37 / 0 / 2 | 0.920 | 37 / 0 |
| v5_image_text | 0.852 | 1.000 | 0.992 | 0.081 | 36 / 0 / 0 | 0.870 | 37 / 0 |
| v5_image_text + platt(CV) | 0.918 | 0.949 | 0.988 | 0.045 | 52 / 0 / 1 | 0.875 | 53 / 0 |
| j_first70 | 0.738 | 0.900 | 0.945 | 0.087 | 18 / 0 / 0 | 0.830 | 23 / 0 |
| j_first70 + platt(CV) | 0.902 | 0.859 | 0.943 | 0.088 | 35 / 0 / 1 | 0.955 | 29 / 0 |
| j_last70 | 0.787 | 0.857 | 0.920 | 0.102 | 19 / 0 / 0 | 0.785 | 26 / 0 |
| j_last70 + platt(CV) | 0.885 | 0.831 | 0.914 | 0.104 | 26 / 3 / 0 | 0.950 | 24 / 0 |
| j_mid70 | 0.754 | 0.920 | 0.930 | 0.083 | 17 / 0 / 0 | 0.835 | 25 / 0 |
| j_mid70 + platt(CV) | 0.852 | 0.800 | 0.926 | 0.085 | 30 / 1 / 0 | 0.985 | 16 / 0 |
| j_trim80 | (running: 25/120) |||||||
| c_text | 0.934 | 0.838 | 0.952 | 0.099 | 22 / 0 / 0 | 0.735 | 36 / 0 |
| c_text + platt(CV) | 0.918 | 0.848 | 0.949 | 0.095 | 37 / 0 / 2 | 0.920 | 36 / 0 |
