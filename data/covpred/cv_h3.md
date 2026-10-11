# Grouped-CV learnability check — h3 (dev repo), exploratory

double-held-out: fold k evals only on held-out tests x held-out files; train excludes both dims.

no-fingerprint drops func_size, file_size, fan_in, fan_out, exports_hit_frac.

| grouping | features | pooled AP model | pooled AP C5 | per-test model | per-test C5 | per-func model | per-func C5 | per-snap model | per-snap C5 |
|---|---|---|---|---|---|---|---|---|---|
| by source file | 0.613 | 0.448 | 0.606 | 0.489 | 0.726 | 0.668 | 0.685 | 0.613 |
| by test file | 0.848 | 0.438 | 0.837 | 0.560 | 0.813 | 0.635 | 0.843 | 0.587 |
| by test file, no-fingerprint | 0.722 | 0.438 | 0.710 | 0.560 | 0.735 | 0.635 | 0.711 | 0.587 |
| double-held-out | 0.566 | 0.428 | 0.569 | 0.470 | 0.666 | 0.636 | 0.651 | 0.597 |
| double-held-out, no-fingerprint | 0.608 | 0.428 | 0.568 | 0.470 | 0.698 | 0.636 | 0.639 | 0.597 |
