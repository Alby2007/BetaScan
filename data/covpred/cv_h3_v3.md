# Grouped-CV learnability check — h3 (dev repo), exploratory

double-held-out: fold k evals only on held-out tests x held-out files; train excludes both dims.

no-fingerprint drops func_size, file_size, fan_in, fan_out, exports_hit_frac.

| grouping | features | pooled AP model | pooled AP C5 | per-test model | per-test C5 | per-func model | per-func C5 | per-snap model | per-snap C5 |
|---|---|---|---|---|---|---|---|---|---|
| by source file | 0.602 | 0.451 | 0.599 | 0.498 | 0.733 | 0.691 | 0.680 | 0.617 |
| by test file | 0.859 | 0.439 | 0.849 | 0.569 | 0.825 | 0.644 | 0.848 | 0.589 |
| by test file, no-fingerprint | 0.719 | 0.439 | 0.710 | 0.569 | 0.739 | 0.644 | 0.703 | 0.589 |
| double-held-out | 0.558 | 0.432 | 0.563 | 0.480 | 0.673 | 0.654 | 0.637 | 0.601 |
| double-held-out, no-fingerprint | 0.598 | 0.432 | 0.566 | 0.480 | 0.709 | 0.654 | 0.614 | 0.601 |
