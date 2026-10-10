# M3 baseline results

parents: 7 (train 6, test 1); mutants: all 141, train 133, test 8, test-with-unseen-file 0; killed in test 4, strict 0

### TEST split (temporal), B2 trained on earlier parents -- candidates = full suite

recall@1/3/5 and hit@3 average only over mutants with more covering tests than k (otherwise any ordering finds everything).

| bucket | ranker | n | recall@1 | recall@3 | recall@5 | recall@5% | recall@10% | recall@20% | hit@3 | hit@10% | APFD | time_frac_95 | n95 | n95_vs_B5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | B0 random | 4 | 0.000 | 0.025 | 0.025 | 0.025 | 0.050 | 0.092 | 0.050 | 0.100 | 0.362 | 1.000 | 74.700 | 2.294 |
| all | B1 import-proximity | 4 | 0.025 | 0.025 | 0.050 | 0.067 | 0.092 | 0.233 | 0.050 | 0.200 | 0.728 | 1.000 | 35.450 | 1.187 |
| all | B2 history co-failure | 4 | 0.000 | 0.333 | 0.333 | 0.333 | 0.583 | 0.667 | 0.500 | 0.750 | 0.813 | 1.000 | 33.650 | 1.376 |
| all | B4 reverse-call reachability | 4 | 0.108 | 0.108 | 0.233 | 0.333 | 0.425 | 0.533 | 0.300 | 0.650 | 0.800 | 1.000 | 29.850 | 1.047 |
| all | B5a coverage, random order | 4 | 0.025 | 0.042 | 0.067 | 0.083 | 0.258 | 0.400 | 0.100 | 0.400 | 0.776 | 1.000 | 26.350 | 0.746 |
| all | B5b coverage, most targeted first | 4 | 0.025 | 0.042 | 0.067 | 0.083 | 0.258 | 0.400 | 0.100 | 0.400 | 0.776 | 1.000 | 26.350 | 0.746 |
| all | B5c coverage, historical failure order | 4 | 0.000 | 0.333 | 0.333 | 0.333 | 0.583 | 0.750 | 0.500 | 0.750 | 0.877 | 1.000 | 15.250 | 0.500 |
| all | B5d coverage, broadest first | 4 | 0.025 | 0.042 | 0.067 | 0.083 | 0.258 | 0.400 | 0.100 | 0.400 | 0.776 | 1.000 | 26.350 | 0.746 |
| all | B6 call distance, ties broadest first | 4 | 0.083 | 0.108 | 0.208 | 0.308 | 0.383 | 0.425 | 0.300 | 0.600 | 0.575 | 1.000 | 55.750 | 1.768 |
| all | B7 lexical overlap | 4 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.333 | 0.000 | 0.000 | 0.499 | 1.000 | 62.450 | 1.925 |
| all | ORACLE (perfect order) | 4 | 0.708 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.991 | 1.000 | 1.750 | 0.061 |
| cov>=2 | B0 random | 4 | 0.000 | 0.025 | 0.025 | 0.025 | 0.050 | 0.092 | 0.050 | 0.100 | 0.362 | 1.000 | 74.700 | 2.294 |
| cov>=2 | B1 import-proximity | 4 | 0.025 | 0.025 | 0.050 | 0.067 | 0.092 | 0.233 | 0.050 | 0.200 | 0.728 | 1.000 | 35.450 | 1.187 |
| cov>=2 | B2 history co-failure | 4 | 0.000 | 0.333 | 0.333 | 0.333 | 0.583 | 0.667 | 0.500 | 0.750 | 0.813 | 1.000 | 33.650 | 1.376 |
| cov>=2 | B4 reverse-call reachability | 4 | 0.108 | 0.108 | 0.233 | 0.333 | 0.425 | 0.533 | 0.300 | 0.650 | 0.800 | 1.000 | 29.850 | 1.047 |
| cov>=2 | B5a coverage, random order | 4 | 0.025 | 0.042 | 0.067 | 0.083 | 0.258 | 0.400 | 0.100 | 0.400 | 0.776 | 1.000 | 26.350 | 0.746 |
| cov>=2 | B5b coverage, most targeted first | 4 | 0.025 | 0.042 | 0.067 | 0.083 | 0.258 | 0.400 | 0.100 | 0.400 | 0.776 | 1.000 | 26.350 | 0.746 |
| cov>=2 | B5c coverage, historical failure order | 4 | 0.000 | 0.333 | 0.333 | 0.333 | 0.583 | 0.750 | 0.500 | 0.750 | 0.877 | 1.000 | 15.250 | 0.500 |
| cov>=2 | B5d coverage, broadest first | 4 | 0.025 | 0.042 | 0.067 | 0.083 | 0.258 | 0.400 | 0.100 | 0.400 | 0.776 | 1.000 | 26.350 | 0.746 |
| cov>=2 | B6 call distance, ties broadest first | 4 | 0.083 | 0.108 | 0.208 | 0.308 | 0.383 | 0.425 | 0.300 | 0.600 | 0.575 | 1.000 | 55.750 | 1.768 |
| cov>=2 | B7 lexical overlap | 4 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.333 | 0.000 | 0.000 | 0.499 | 1.000 | 62.450 | 1.925 |
| cov>=2 | ORACLE (perfect order) | 4 | 0.708 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.991 | 1.000 | 1.750 | 0.061 |
| cov=>10 | B0 random | 4 | 0.000 | 0.025 | 0.025 | 0.025 | 0.050 | 0.092 | 0.050 | 0.100 | 0.362 | 1.000 | 74.700 | 2.294 |
| cov=>10 | B1 import-proximity | 4 | 0.025 | 0.025 | 0.050 | 0.067 | 0.092 | 0.233 | 0.050 | 0.200 | 0.728 | 1.000 | 35.450 | 1.187 |
| cov=>10 | B2 history co-failure | 4 | 0.000 | 0.333 | 0.333 | 0.333 | 0.583 | 0.667 | 0.500 | 0.750 | 0.813 | 1.000 | 33.650 | 1.376 |
| cov=>10 | B4 reverse-call reachability | 4 | 0.108 | 0.108 | 0.233 | 0.333 | 0.425 | 0.533 | 0.300 | 0.650 | 0.800 | 1.000 | 29.850 | 1.047 |
| cov=>10 | B5a coverage, random order | 4 | 0.025 | 0.042 | 0.067 | 0.083 | 0.258 | 0.400 | 0.100 | 0.400 | 0.776 | 1.000 | 26.350 | 0.746 |
| cov=>10 | B5b coverage, most targeted first | 4 | 0.025 | 0.042 | 0.067 | 0.083 | 0.258 | 0.400 | 0.100 | 0.400 | 0.776 | 1.000 | 26.350 | 0.746 |
| cov=>10 | B5c coverage, historical failure order | 4 | 0.000 | 0.333 | 0.333 | 0.333 | 0.583 | 0.750 | 0.500 | 0.750 | 0.877 | 1.000 | 15.250 | 0.500 |
| cov=>10 | B5d coverage, broadest first | 4 | 0.025 | 0.042 | 0.067 | 0.083 | 0.258 | 0.400 | 0.100 | 0.400 | 0.776 | 1.000 | 26.350 | 0.746 |
| cov=>10 | B6 call distance, ties broadest first | 4 | 0.083 | 0.108 | 0.208 | 0.308 | 0.383 | 0.425 | 0.300 | 0.600 | 0.575 | 1.000 | 55.750 | 1.768 |
| cov=>10 | B7 lexical overlap | 4 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.333 | 0.000 | 0.000 | 0.499 | 1.000 | 62.450 | 1.925 |
| cov=>10 | ORACLE (perfect order) | 4 | 0.708 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.991 | 1.000 | 1.750 | 0.061 |

### TEST split (temporal), B2 trained on earlier parents -- candidates = covering tests only

recall@1/3/5 and hit@3 average only over mutants with more covering tests than k (otherwise any ordering finds everything).

| bucket | ranker | n | recall@1 | recall@3 | recall@5 | recall@5% | recall@10% | recall@20% | hit@3 | hit@10% | APFD | time_frac_95 | n95 | n95_vs_B5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | B0 random | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| all | B1 import-proximity | 4 | 0.025 | 0.058 | 0.083 | 0.025 | 0.083 | 0.108 | 0.150 | 0.200 | 0.540 | 1.000 | 19.650 | 0.584 |
| all | B2 history co-failure | 4 | 0.000 | 0.333 | 0.333 | 0.208 | 0.333 | 0.333 | 0.500 | 0.500 | 0.626 | 1.000 | 15.250 | 0.500 |
| all | B4 reverse-call reachability | 4 | 0.108 | 0.108 | 0.250 | 0.108 | 0.133 | 0.425 | 0.300 | 0.350 | 0.650 | 1.000 | 16.200 | 0.498 |
| all | B5a coverage, random order | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| all | B5b coverage, most targeted first | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| all | B5c coverage, historical failure order | 4 | 0.000 | 0.333 | 0.333 | 0.208 | 0.333 | 0.333 | 0.500 | 0.500 | 0.626 | 1.000 | 15.250 | 0.500 |
| all | B5d coverage, broadest first | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| all | B6 call distance, ties broadest first | 4 | 0.108 | 0.125 | 0.250 | 0.108 | 0.125 | 0.400 | 0.300 | 0.300 | 0.557 | 1.000 | 20.050 | 0.577 |
| all | B7 lexical overlap | 4 | 0.000 | 0.083 | 0.267 | 0.050 | 0.083 | 0.417 | 0.250 | 0.250 | 0.529 | 1.000 | 21.250 | 0.605 |
| all | ORACLE (perfect order) | 4 | 0.708 | 1.000 | 1.000 | 0.917 | 1.000 | 1.000 | 1.000 | 1.000 | 0.970 | 1.000 | 1.750 | 0.061 |
| cov>=2 | B0 random | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| cov>=2 | B1 import-proximity | 4 | 0.025 | 0.058 | 0.083 | 0.025 | 0.083 | 0.108 | 0.150 | 0.200 | 0.540 | 1.000 | 19.650 | 0.584 |
| cov>=2 | B2 history co-failure | 4 | 0.000 | 0.333 | 0.333 | 0.208 | 0.333 | 0.333 | 0.500 | 0.500 | 0.626 | 1.000 | 15.250 | 0.500 |
| cov>=2 | B4 reverse-call reachability | 4 | 0.108 | 0.108 | 0.250 | 0.108 | 0.133 | 0.425 | 0.300 | 0.350 | 0.650 | 1.000 | 16.200 | 0.498 |
| cov>=2 | B5a coverage, random order | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| cov>=2 | B5b coverage, most targeted first | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| cov>=2 | B5c coverage, historical failure order | 4 | 0.000 | 0.333 | 0.333 | 0.208 | 0.333 | 0.333 | 0.500 | 0.500 | 0.626 | 1.000 | 15.250 | 0.500 |
| cov>=2 | B5d coverage, broadest first | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| cov>=2 | B6 call distance, ties broadest first | 4 | 0.108 | 0.125 | 0.250 | 0.108 | 0.125 | 0.400 | 0.300 | 0.300 | 0.557 | 1.000 | 20.050 | 0.577 |
| cov>=2 | B7 lexical overlap | 4 | 0.000 | 0.083 | 0.267 | 0.050 | 0.083 | 0.417 | 0.250 | 0.250 | 0.529 | 1.000 | 21.250 | 0.605 |
| cov>=2 | ORACLE (perfect order) | 4 | 0.708 | 1.000 | 1.000 | 0.917 | 1.000 | 1.000 | 1.000 | 1.000 | 0.970 | 1.000 | 1.750 | 0.061 |
| cov=>10 | B0 random | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| cov=>10 | B1 import-proximity | 4 | 0.025 | 0.058 | 0.083 | 0.025 | 0.083 | 0.108 | 0.150 | 0.200 | 0.540 | 1.000 | 19.650 | 0.584 |
| cov=>10 | B2 history co-failure | 4 | 0.000 | 0.333 | 0.333 | 0.208 | 0.333 | 0.333 | 0.500 | 0.500 | 0.626 | 1.000 | 15.250 | 0.500 |
| cov=>10 | B4 reverse-call reachability | 4 | 0.108 | 0.108 | 0.250 | 0.108 | 0.133 | 0.425 | 0.300 | 0.350 | 0.650 | 1.000 | 16.200 | 0.498 |
| cov=>10 | B5a coverage, random order | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| cov=>10 | B5b coverage, most targeted first | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| cov=>10 | B5c coverage, historical failure order | 4 | 0.000 | 0.333 | 0.333 | 0.208 | 0.333 | 0.333 | 0.500 | 0.500 | 0.626 | 1.000 | 15.250 | 0.500 |
| cov=>10 | B5d coverage, broadest first | 4 | 0.025 | 0.042 | 0.067 | 0.042 | 0.042 | 0.067 | 0.100 | 0.100 | 0.374 | 1.000 | 26.350 | 0.746 |
| cov=>10 | B6 call distance, ties broadest first | 4 | 0.108 | 0.125 | 0.250 | 0.108 | 0.125 | 0.400 | 0.300 | 0.300 | 0.557 | 1.000 | 20.050 | 0.577 |
| cov=>10 | B7 lexical overlap | 4 | 0.000 | 0.083 | 0.267 | 0.050 | 0.083 | 0.417 | 0.250 | 0.250 | 0.529 | 1.000 | 21.250 | 0.605 |
| cov=>10 | ORACLE (perfect order) | 4 | 0.708 | 1.000 | 1.000 | 0.917 | 1.000 | 1.000 | 1.000 | 1.000 | 0.970 | 1.000 | 1.750 | 0.061 |

### TEST split restricted to files unseen in train (no same-file leakage) -- candidates = full suite

recall@1/3/5 and hit@3 average only over mutants with more covering tests than k (otherwise any ordering finds everything).

| bucket | ranker | n | recall@1 | recall@3 | recall@5 | recall@5% | recall@10% | recall@20% | hit@3 | hit@10% | APFD | time_frac_95 | n95 | n95_vs_B5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

### TEST split restricted to files unseen in train (no same-file leakage) -- candidates = covering tests only

recall@1/3/5 and hit@3 average only over mutants with more covering tests than k (otherwise any ordering finds everything).

| bucket | ranker | n | recall@1 | recall@3 | recall@5 | recall@5% | recall@10% | recall@20% | hit@3 | hit@10% | APFD | time_frac_95 | n95 | n95_vs_B5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

### ALL mutants (no training needed; B2 omitted) -- candidates = full suite

recall@1/3/5 and hit@3 average only over mutants with more covering tests than k (otherwise any ordering finds everything).

| bucket | ranker | n | recall@1 | recall@3 | recall@5 | recall@5% | recall@10% | recall@20% | hit@3 | hit@10% | APFD | time_frac_95 | n95 | n95_vs_B5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | B0 random | 113 | 0.010 | 0.029 | 0.046 | 0.046 | 0.095 | 0.189 | 0.389 | 0.593 | 0.487 | 0.897 | 81.942 | 2.420 |
| all | B1 import-proximity | 113 | 0.117 | 0.159 | 0.199 | 0.200 | 0.301 | 0.496 | 0.733 | 0.867 | 0.762 | 0.779 | 46.639 | 1.476 |
| all | B4 reverse-call reachability | 113 | 0.144 | 0.241 | 0.305 | 0.308 | 0.413 | 0.596 | 0.846 | 0.931 | 0.809 | 0.746 | 38.812 | 1.189 |
| all | B5a coverage, random order | 113 | 0.031 | 0.076 | 0.138 | 0.139 | 0.284 | 0.536 | 0.589 | 0.761 | 0.777 | 0.679 | 35.609 | 0.849 |
| all | B5b coverage, most targeted first | 113 | 0.063 | 0.109 | 0.192 | 0.193 | 0.314 | 0.510 | 0.604 | 0.743 | 0.771 | 0.662 | 34.823 | 0.836 |
| all | B5d coverage, broadest first | 113 | 0.039 | 0.124 | 0.199 | 0.199 | 0.342 | 0.560 | 0.692 | 0.788 | 0.790 | 0.695 | 34.212 | 0.821 |
| all | B6 call distance, ties broadest first | 113 | 0.069 | 0.196 | 0.267 | 0.270 | 0.389 | 0.550 | 0.793 | 0.858 | 0.757 | 0.742 | 44.892 | 1.324 |
| all | B7 lexical overlap | 113 | 0.082 | 0.100 | 0.130 | 0.130 | 0.169 | 0.279 | 0.382 | 0.588 | 0.545 | 0.859 | 74.758 | 2.245 |
| all | ORACLE (perfect order) | 113 | 0.278 | 0.459 | 0.552 | 0.552 | 0.699 | 0.860 | 1.000 | 1.000 | 0.914 | 0.522 | 16.327 | 0.444 |
| cov>=2 | B0 random | 113 | 0.010 | 0.029 | 0.046 | 0.046 | 0.095 | 0.189 | 0.389 | 0.593 | 0.487 | 0.897 | 81.942 | 2.420 |
| cov>=2 | B1 import-proximity | 113 | 0.117 | 0.159 | 0.199 | 0.200 | 0.301 | 0.496 | 0.733 | 0.867 | 0.762 | 0.779 | 46.639 | 1.476 |
| cov>=2 | B4 reverse-call reachability | 113 | 0.144 | 0.241 | 0.305 | 0.308 | 0.413 | 0.596 | 0.846 | 0.931 | 0.809 | 0.746 | 38.812 | 1.189 |
| cov>=2 | B5a coverage, random order | 113 | 0.031 | 0.076 | 0.138 | 0.139 | 0.284 | 0.536 | 0.589 | 0.761 | 0.777 | 0.679 | 35.609 | 0.849 |
| cov>=2 | B5b coverage, most targeted first | 113 | 0.063 | 0.109 | 0.192 | 0.193 | 0.314 | 0.510 | 0.604 | 0.743 | 0.771 | 0.662 | 34.823 | 0.836 |
| cov>=2 | B5d coverage, broadest first | 113 | 0.039 | 0.124 | 0.199 | 0.199 | 0.342 | 0.560 | 0.692 | 0.788 | 0.790 | 0.695 | 34.212 | 0.821 |
| cov>=2 | B6 call distance, ties broadest first | 113 | 0.069 | 0.196 | 0.267 | 0.270 | 0.389 | 0.550 | 0.793 | 0.858 | 0.757 | 0.742 | 44.892 | 1.324 |
| cov>=2 | B7 lexical overlap | 113 | 0.082 | 0.100 | 0.130 | 0.130 | 0.169 | 0.279 | 0.382 | 0.588 | 0.545 | 0.859 | 74.758 | 2.245 |
| cov>=2 | ORACLE (perfect order) | 113 | 0.278 | 0.459 | 0.552 | 0.552 | 0.699 | 0.860 | 1.000 | 1.000 | 0.914 | 0.522 | 16.327 | 0.444 |
| cov=>10 | B0 random | 113 | 0.010 | 0.029 | 0.046 | 0.046 | 0.095 | 0.189 | 0.389 | 0.593 | 0.487 | 0.897 | 81.942 | 2.420 |
| cov=>10 | B1 import-proximity | 113 | 0.117 | 0.159 | 0.199 | 0.200 | 0.301 | 0.496 | 0.733 | 0.867 | 0.762 | 0.779 | 46.639 | 1.476 |
| cov=>10 | B4 reverse-call reachability | 113 | 0.144 | 0.241 | 0.305 | 0.308 | 0.413 | 0.596 | 0.846 | 0.931 | 0.809 | 0.746 | 38.812 | 1.189 |
| cov=>10 | B5a coverage, random order | 113 | 0.031 | 0.076 | 0.138 | 0.139 | 0.284 | 0.536 | 0.589 | 0.761 | 0.777 | 0.679 | 35.609 | 0.849 |
| cov=>10 | B5b coverage, most targeted first | 113 | 0.063 | 0.109 | 0.192 | 0.193 | 0.314 | 0.510 | 0.604 | 0.743 | 0.771 | 0.662 | 34.823 | 0.836 |
| cov=>10 | B5d coverage, broadest first | 113 | 0.039 | 0.124 | 0.199 | 0.199 | 0.342 | 0.560 | 0.692 | 0.788 | 0.790 | 0.695 | 34.212 | 0.821 |
| cov=>10 | B6 call distance, ties broadest first | 113 | 0.069 | 0.196 | 0.267 | 0.270 | 0.389 | 0.550 | 0.793 | 0.858 | 0.757 | 0.742 | 44.892 | 1.324 |
| cov=>10 | B7 lexical overlap | 113 | 0.082 | 0.100 | 0.130 | 0.130 | 0.169 | 0.279 | 0.382 | 0.588 | 0.545 | 0.859 | 74.758 | 2.245 |
| cov=>10 | ORACLE (perfect order) | 113 | 0.278 | 0.459 | 0.552 | 0.552 | 0.699 | 0.860 | 1.000 | 1.000 | 0.914 | 0.522 | 16.327 | 0.444 |

### ALL mutants (no training needed; B2 omitted) -- candidates = covering tests only

recall@1/3/5 and hit@3 average only over mutants with more covering tests than k (otherwise any ordering finds everything).

| bucket | ranker | n | recall@1 | recall@3 | recall@5 | recall@5% | recall@10% | recall@20% | hit@3 | hit@10% | APFD | time_frac_95 | n95 | n95_vs_B5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | B0 random | 113 | 0.031 | 0.076 | 0.138 | 0.057 | 0.114 | 0.196 | 0.589 | 0.653 | 0.488 | 0.903 | 35.609 | 0.849 |
| all | B1 import-proximity | 113 | 0.132 | 0.198 | 0.257 | 0.173 | 0.229 | 0.339 | 0.804 | 0.839 | 0.606 | 0.842 | 28.869 | 0.727 |
| all | B4 reverse-call reachability | 113 | 0.148 | 0.260 | 0.333 | 0.222 | 0.302 | 0.411 | 0.881 | 0.904 | 0.637 | 0.825 | 27.696 | 0.698 |
| all | B5a coverage, random order | 113 | 0.031 | 0.076 | 0.138 | 0.057 | 0.114 | 0.196 | 0.589 | 0.653 | 0.488 | 0.903 | 35.609 | 0.849 |
| all | B5b coverage, most targeted first | 113 | 0.063 | 0.109 | 0.192 | 0.117 | 0.159 | 0.220 | 0.604 | 0.657 | 0.476 | 0.881 | 34.823 | 0.836 |
| all | B5d coverage, broadest first | 113 | 0.039 | 0.124 | 0.199 | 0.099 | 0.157 | 0.264 | 0.692 | 0.701 | 0.517 | 0.923 | 34.212 | 0.821 |
| all | B6 call distance, ties broadest first | 113 | 0.073 | 0.208 | 0.296 | 0.176 | 0.250 | 0.370 | 0.809 | 0.821 | 0.590 | 0.873 | 31.650 | 0.754 |
| all | B7 lexical overlap | 113 | 0.110 | 0.185 | 0.248 | 0.151 | 0.197 | 0.316 | 0.653 | 0.735 | 0.555 | 0.870 | 32.149 | 0.781 |
| all | ORACLE (perfect order) | 113 | 0.278 | 0.459 | 0.552 | 0.414 | 0.511 | 0.639 | 1.000 | 1.000 | 0.772 | 0.671 | 16.327 | 0.444 |
| cov>=2 | B0 random | 113 | 0.031 | 0.076 | 0.138 | 0.057 | 0.114 | 0.196 | 0.589 | 0.653 | 0.488 | 0.903 | 35.609 | 0.849 |
| cov>=2 | B1 import-proximity | 113 | 0.132 | 0.198 | 0.257 | 0.173 | 0.229 | 0.339 | 0.804 | 0.839 | 0.606 | 0.842 | 28.869 | 0.727 |
| cov>=2 | B4 reverse-call reachability | 113 | 0.148 | 0.260 | 0.333 | 0.222 | 0.302 | 0.411 | 0.881 | 0.904 | 0.637 | 0.825 | 27.696 | 0.698 |
| cov>=2 | B5a coverage, random order | 113 | 0.031 | 0.076 | 0.138 | 0.057 | 0.114 | 0.196 | 0.589 | 0.653 | 0.488 | 0.903 | 35.609 | 0.849 |
| cov>=2 | B5b coverage, most targeted first | 113 | 0.063 | 0.109 | 0.192 | 0.117 | 0.159 | 0.220 | 0.604 | 0.657 | 0.476 | 0.881 | 34.823 | 0.836 |
| cov>=2 | B5d coverage, broadest first | 113 | 0.039 | 0.124 | 0.199 | 0.099 | 0.157 | 0.264 | 0.692 | 0.701 | 0.517 | 0.923 | 34.212 | 0.821 |
| cov>=2 | B6 call distance, ties broadest first | 113 | 0.073 | 0.208 | 0.296 | 0.176 | 0.250 | 0.370 | 0.809 | 0.821 | 0.590 | 0.873 | 31.650 | 0.754 |
| cov>=2 | B7 lexical overlap | 113 | 0.110 | 0.185 | 0.248 | 0.151 | 0.197 | 0.316 | 0.653 | 0.735 | 0.555 | 0.870 | 32.149 | 0.781 |
| cov>=2 | ORACLE (perfect order) | 113 | 0.278 | 0.459 | 0.552 | 0.414 | 0.511 | 0.639 | 1.000 | 1.000 | 0.772 | 0.671 | 16.327 | 0.444 |
| cov=>10 | B0 random | 113 | 0.031 | 0.076 | 0.138 | 0.057 | 0.114 | 0.196 | 0.589 | 0.653 | 0.488 | 0.903 | 35.609 | 0.849 |
| cov=>10 | B1 import-proximity | 113 | 0.132 | 0.198 | 0.257 | 0.173 | 0.229 | 0.339 | 0.804 | 0.839 | 0.606 | 0.842 | 28.869 | 0.727 |
| cov=>10 | B4 reverse-call reachability | 113 | 0.148 | 0.260 | 0.333 | 0.222 | 0.302 | 0.411 | 0.881 | 0.904 | 0.637 | 0.825 | 27.696 | 0.698 |
| cov=>10 | B5a coverage, random order | 113 | 0.031 | 0.076 | 0.138 | 0.057 | 0.114 | 0.196 | 0.589 | 0.653 | 0.488 | 0.903 | 35.609 | 0.849 |
| cov=>10 | B5b coverage, most targeted first | 113 | 0.063 | 0.109 | 0.192 | 0.117 | 0.159 | 0.220 | 0.604 | 0.657 | 0.476 | 0.881 | 34.823 | 0.836 |
| cov=>10 | B5d coverage, broadest first | 113 | 0.039 | 0.124 | 0.199 | 0.099 | 0.157 | 0.264 | 0.692 | 0.701 | 0.517 | 0.923 | 34.212 | 0.821 |
| cov=>10 | B6 call distance, ties broadest first | 113 | 0.073 | 0.208 | 0.296 | 0.176 | 0.250 | 0.370 | 0.809 | 0.821 | 0.590 | 0.873 | 31.650 | 0.754 |
| cov=>10 | B7 lexical overlap | 113 | 0.110 | 0.185 | 0.248 | 0.151 | 0.197 | 0.316 | 0.653 | 0.735 | 0.555 | 0.870 | 32.149 | 0.781 |
| cov=>10 | ORACLE (perfect order) | 113 | 0.278 | 0.459 | 0.552 | 0.414 | 0.511 | 0.639 | 1.000 | 1.000 | 0.772 | 0.671 | 16.327 | 0.444 |

## Oracle headroom: failing fraction = failing tests / covering tests (killed mutants, all 337)

Oracle n95/ncov is ceil(0.95*failing)/covering, so it is bounded below by this fraction. Median above 0.7 means little headroom inside the covering set.

| stratum | n | median | p25 | p75 | mean | oracle n95/ncov (mean) | flag median>0.7 |
|---|---|---|---|---|---|---|---|
| >10 | 113 | 0.30 | 0.06 | 0.89 | 0.46 | 0.44 | no |
| >=2 | 113 | 0.30 | 0.06 | 0.89 | 0.46 | 0.44 | no |

## Cluster-bootstrap 95% CIs (resample the 12 parent commits; ALL mutants, training-free rankers; full-suite candidates)

Mutants from one commit are correlated, so the effective n is the number of commits (12). Differences are paired per mutant. Test-split-only CIs would have 4 clusters and are not reported.

| stratum | metric | ranker | mean [95% CI] | paired diff vs B5a [95% CI] | paired diff vs B4 [95% CI] |
|---|---|---|---|---|---|
| >=2 | n95_vs_B5 | ORACLE | 0.444 [0.389, 0.488] | -0.405 [-0.440, -0.379] | -0.745 [-0.887, -0.642] |
| >=2 | n95_vs_B5 | B5a coverage | 0.849 [0.823, 0.871] | - | -0.340 [-0.487, -0.233] |
| >=2 | n95_vs_B5 | B5b coverage | 0.836 [0.809, 0.868] | -0.012 [-0.033, +0.009] | -0.353 [-0.499, -0.239] |
| >=2 | n95_vs_B5 | B4 reverse-call reachability | 1.189 [1.063, 1.348] | +0.340 [+0.233, +0.490] | - |
| >=2 | n95_vs_B5 | B1 import-proximity | 1.476 [1.389, 1.602] | +0.627 [+0.545, +0.743] | +0.287 [+0.222, +0.355] |
| >=2 | recall@5 | ORACLE | 0.552 [0.514, 0.618] | +0.414 [+0.375, +0.480] | +0.248 [+0.206, +0.322] |
| >=2 | recall@5 | B5a coverage | 0.138 [0.122, 0.155] | - | -0.167 [-0.189, -0.135] |
| >=2 | recall@5 | B5b coverage | 0.192 [0.158, 0.222] | +0.054 [+0.022, +0.083] | -0.112 [-0.150, -0.072] |
| >=2 | recall@5 | B4 reverse-call reachability | 0.305 [0.282, 0.321] | +0.167 [+0.135, +0.189] | - |
| >=2 | recall@5 | B1 import-proximity | 0.199 [0.175, 0.221] | +0.061 [+0.040, +0.077] | -0.105 [-0.126, -0.083] |
| >=2 | APFD | ORACLE | 0.914 [0.903, 0.926] | +0.137 [+0.125, +0.149] | +0.105 [+0.097, +0.120] |
| >=2 | APFD | B5a coverage | 0.777 [0.766, 0.788] | - | -0.032 [-0.044, -0.009] |
| >=2 | APFD | B5b coverage | 0.771 [0.746, 0.790] | -0.006 [-0.021, +0.004] | -0.038 [-0.058, -0.012] |
| >=2 | APFD | B4 reverse-call reachability | 0.809 [0.792, 0.820] | +0.032 [+0.009, +0.044] | - |
| >=2 | APFD | B1 import-proximity | 0.762 [0.745, 0.777] | -0.015 [-0.033, -0.003] | -0.048 [-0.055, -0.039] |
| >10 | n95_vs_B5 | ORACLE | 0.444 [0.389, 0.488] | -0.405 [-0.440, -0.379] | -0.745 [-0.887, -0.642] |
| >10 | n95_vs_B5 | B5a coverage | 0.849 [0.823, 0.871] | - | -0.340 [-0.487, -0.233] |
| >10 | n95_vs_B5 | B5b coverage | 0.836 [0.809, 0.868] | -0.012 [-0.033, +0.009] | -0.353 [-0.499, -0.239] |
| >10 | n95_vs_B5 | B4 reverse-call reachability | 1.189 [1.063, 1.348] | +0.340 [+0.233, +0.490] | - |
| >10 | n95_vs_B5 | B1 import-proximity | 1.476 [1.389, 1.602] | +0.627 [+0.545, +0.743] | +0.287 [+0.222, +0.355] |
| >10 | recall@5 | ORACLE | 0.552 [0.514, 0.618] | +0.414 [+0.375, +0.480] | +0.248 [+0.206, +0.322] |
| >10 | recall@5 | B5a coverage | 0.138 [0.122, 0.155] | - | -0.167 [-0.189, -0.135] |
| >10 | recall@5 | B5b coverage | 0.192 [0.158, 0.222] | +0.054 [+0.022, +0.083] | -0.112 [-0.150, -0.072] |
| >10 | recall@5 | B4 reverse-call reachability | 0.305 [0.282, 0.321] | +0.167 [+0.135, +0.189] | - |
| >10 | recall@5 | B1 import-proximity | 0.199 [0.175, 0.221] | +0.061 [+0.040, +0.077] | -0.105 [-0.126, -0.083] |
| >10 | APFD | ORACLE | 0.914 [0.903, 0.926] | +0.137 [+0.125, +0.149] | +0.105 [+0.097, +0.120] |
| >10 | APFD | B5a coverage | 0.777 [0.766, 0.788] | - | -0.032 [-0.044, -0.009] |
| >10 | APFD | B5b coverage | 0.771 [0.746, 0.790] | -0.006 [-0.021, +0.004] | -0.038 [-0.058, -0.012] |
| >10 | APFD | B4 reverse-call reachability | 0.809 [0.792, 0.820] | +0.032 [+0.009, +0.044] | - |
| >10 | APFD | B1 import-proximity | 0.762 [0.745, 0.777] | -0.015 [-0.033, -0.003] | -0.048 [-0.055, -0.039] |

## M4 go/no-go (stratum >10 covering tests)

Rule: GO iff oracle n95/ncov < 0.5 AND B5a n95/ncov > 0.7 (B5a wastes most of the covering set). Commit-clustered 95% CIs shown; verdict uses point estimates and also says whether the CI agrees.

- killed mutants in stratum: 113 from 7 commits
- oracle n95/ncov: 0.444 [0.389, 0.488]
- B5a n95/ncov: 0.849 [0.823, 0.871]
- VERDICT (point estimates): GO; CIs agree

## Inside the covering set: commit-clustered bootstrap CIs (ALL mutants, candidates = covering tests only)

| stratum | metric | ranker | mean [95% CI] | paired diff vs B5a [95% CI] | paired diff vs B4 [95% CI] |
|---|---|---|---|---|---|
| >10 | n95 | ORACLE | 16.327 [14.080, 18.232] | -19.281 [-20.768, -17.432] | -11.368 [-13.264, -9.486] |
| >10 | n95 | B5a coverage | 35.609 [33.208, 37.726] | - | - |
| >10 | n95 | B5b coverage | 34.823 [31.811, 37.682] | -0.786 [-1.709, +0.221] | +7.127 [+5.825, +8.000] |
| >10 | n95 | B5d coverage | 34.212 [32.086, 35.976] | -1.396 [-2.698, -0.242] | +6.517 [+3.908, +8.615] |
| >10 | n95 | B6 call distance | 31.650 [29.282, 33.653] | -3.959 [-4.918, -2.846] | +3.954 [+1.880, +5.514] |
| >10 | n95 | B4 reverse-call reachability | 27.696 [24.378, 30.953] | -7.913 [-9.569, -5.972] | - |
| >10 | n95 | B1 import-proximity | 28.869 [25.668, 32.349] | -6.740 [-8.347, -4.681] | +1.173 [+0.837, +1.576] |
| >10 | n95 | B7 lexical overlap | 32.149 [29.681, 34.342] | -3.460 [-4.055, -2.600] | +4.453 [+2.877, +5.758] |
| >10 | recall@5 | ORACLE | 0.552 [0.514, 0.618] | +0.414 [+0.375, +0.480] | +0.219 [+0.178, +0.294] |
| >10 | recall@5 | B5a coverage | 0.138 [0.122, 0.155] | - | - |
| >10 | recall@5 | B5b coverage | 0.192 [0.158, 0.222] | +0.054 [+0.022, +0.083] | -0.141 [-0.170, -0.109] |
| >10 | recall@5 | B5d coverage | 0.199 [0.165, 0.226] | +0.061 [+0.020, +0.098] | -0.135 [-0.175, -0.096] |
| >10 | recall@5 | B6 call distance | 0.296 [0.266, 0.318] | +0.158 [+0.114, +0.191] | -0.037 [-0.061, -0.014] |
| >10 | recall@5 | B4 reverse-call reachability | 0.333 [0.314, 0.349] | +0.195 [+0.169, +0.214] | - |
| >10 | recall@5 | B1 import-proximity | 0.257 [0.227, 0.278] | +0.119 [+0.101, +0.132] | -0.076 [-0.101, -0.050] |
| >10 | recall@5 | B7 lexical overlap | 0.248 [0.226, 0.269] | +0.110 [+0.086, +0.130] | -0.085 [-0.102, -0.065] |
| >10 | APFD | ORACLE | 0.772 [0.749, 0.800] | +0.284 [+0.259, +0.321] | +0.135 [+0.118, +0.165] |
| >10 | APFD | B5a coverage | 0.488 [0.472, 0.498] | - | - |
| >10 | APFD | B5b coverage | 0.476 [0.447, 0.499] | -0.012 [-0.039, +0.009] | -0.161 [-0.188, -0.132] |
| >10 | APFD | B5d coverage | 0.517 [0.488, 0.544] | +0.029 [+0.005, +0.055] | -0.120 [-0.157, -0.084] |
| >10 | APFD | B6 call distance | 0.590 [0.568, 0.606] | +0.102 [+0.077, +0.123] | -0.047 [-0.066, -0.025] |
| >10 | APFD | B4 reverse-call reachability | 0.637 [0.615, 0.652] | +0.149 [+0.124, +0.171] | - |
| >10 | APFD | B1 import-proximity | 0.606 [0.581, 0.622] | +0.118 [+0.094, +0.138] | -0.031 [-0.044, -0.021] |
| >10 | APFD | B7 lexical overlap | 0.555 [0.542, 0.565] | +0.067 [+0.055, +0.079] | -0.082 [-0.099, -0.066] |
| >10 | time_frac_95 | ORACLE | 0.671 [0.550, 0.856] | -0.232 [-0.320, -0.104] | -0.154 [-0.213, -0.067] |
| >10 | time_frac_95 | B5a coverage | 0.903 [0.862, 0.960] | - | - |
| >10 | time_frac_95 | B5b coverage | 0.881 [0.825, 0.951] | -0.022 [-0.043, +0.001] | +0.056 [+0.023, +0.082] |
| >10 | time_frac_95 | B5d coverage | 0.923 [0.890, 0.967] | +0.020 [-0.003, +0.046] | +0.098 [+0.037, +0.149] |
| >10 | time_frac_95 | B6 call distance | 0.873 [0.822, 0.945] | -0.030 [-0.048, -0.010] | +0.048 [+0.018, +0.074] |
| >10 | time_frac_95 | B4 reverse-call reachability | 0.825 [0.754, 0.925] | -0.078 [-0.115, -0.032] | - |
| >10 | time_frac_95 | B1 import-proximity | 0.842 [0.775, 0.934] | -0.061 [-0.096, -0.021] | +0.017 [+0.007, +0.027] |
| >10 | time_frac_95 | B7 lexical overlap | 0.870 [0.817, 0.945] | -0.033 [-0.048, -0.014] | +0.045 [+0.013, +0.077] |
| >=2 | n95 | ORACLE | 16.327 [14.080, 18.232] | -19.281 [-20.768, -17.432] | -11.368 [-13.264, -9.486] |
| >=2 | n95 | B5a coverage | 35.609 [33.208, 37.726] | - | - |
| >=2 | n95 | B5b coverage | 34.823 [31.811, 37.682] | -0.786 [-1.709, +0.221] | +7.127 [+5.825, +8.000] |
| >=2 | n95 | B5d coverage | 34.212 [32.086, 35.976] | -1.396 [-2.698, -0.242] | +6.517 [+3.908, +8.615] |
| >=2 | n95 | B6 call distance | 31.650 [29.282, 33.653] | -3.959 [-4.918, -2.846] | +3.954 [+1.880, +5.514] |
| >=2 | n95 | B4 reverse-call reachability | 27.696 [24.378, 30.953] | -7.913 [-9.569, -5.972] | - |
| >=2 | n95 | B1 import-proximity | 28.869 [25.668, 32.349] | -6.740 [-8.347, -4.681] | +1.173 [+0.837, +1.576] |
| >=2 | n95 | B7 lexical overlap | 32.149 [29.681, 34.342] | -3.460 [-4.055, -2.600] | +4.453 [+2.877, +5.758] |
| >=2 | recall@5 | ORACLE | 0.552 [0.514, 0.618] | +0.414 [+0.375, +0.480] | +0.219 [+0.178, +0.294] |
| >=2 | recall@5 | B5a coverage | 0.138 [0.122, 0.155] | - | - |
| >=2 | recall@5 | B5b coverage | 0.192 [0.158, 0.222] | +0.054 [+0.022, +0.083] | -0.141 [-0.170, -0.109] |
| >=2 | recall@5 | B5d coverage | 0.199 [0.165, 0.226] | +0.061 [+0.020, +0.098] | -0.135 [-0.175, -0.096] |
| >=2 | recall@5 | B6 call distance | 0.296 [0.266, 0.318] | +0.158 [+0.114, +0.191] | -0.037 [-0.061, -0.014] |
| >=2 | recall@5 | B4 reverse-call reachability | 0.333 [0.314, 0.349] | +0.195 [+0.169, +0.214] | - |
| >=2 | recall@5 | B1 import-proximity | 0.257 [0.227, 0.278] | +0.119 [+0.101, +0.132] | -0.076 [-0.101, -0.050] |
| >=2 | recall@5 | B7 lexical overlap | 0.248 [0.226, 0.269] | +0.110 [+0.086, +0.130] | -0.085 [-0.102, -0.065] |
| >=2 | APFD | ORACLE | 0.772 [0.749, 0.800] | +0.284 [+0.259, +0.321] | +0.135 [+0.118, +0.165] |
| >=2 | APFD | B5a coverage | 0.488 [0.472, 0.498] | - | - |
| >=2 | APFD | B5b coverage | 0.476 [0.447, 0.499] | -0.012 [-0.039, +0.009] | -0.161 [-0.188, -0.132] |
| >=2 | APFD | B5d coverage | 0.517 [0.488, 0.544] | +0.029 [+0.005, +0.055] | -0.120 [-0.157, -0.084] |
| >=2 | APFD | B6 call distance | 0.590 [0.568, 0.606] | +0.102 [+0.077, +0.123] | -0.047 [-0.066, -0.025] |
| >=2 | APFD | B4 reverse-call reachability | 0.637 [0.615, 0.652] | +0.149 [+0.124, +0.171] | - |
| >=2 | APFD | B1 import-proximity | 0.606 [0.581, 0.622] | +0.118 [+0.094, +0.138] | -0.031 [-0.044, -0.021] |
| >=2 | APFD | B7 lexical overlap | 0.555 [0.542, 0.565] | +0.067 [+0.055, +0.079] | -0.082 [-0.099, -0.066] |
| >=2 | time_frac_95 | ORACLE | 0.671 [0.550, 0.856] | -0.232 [-0.320, -0.104] | -0.154 [-0.213, -0.067] |
| >=2 | time_frac_95 | B5a coverage | 0.903 [0.862, 0.960] | - | - |
| >=2 | time_frac_95 | B5b coverage | 0.881 [0.825, 0.951] | -0.022 [-0.043, +0.001] | +0.056 [+0.023, +0.082] |
| >=2 | time_frac_95 | B5d coverage | 0.923 [0.890, 0.967] | +0.020 [-0.003, +0.046] | +0.098 [+0.037, +0.149] |
| >=2 | time_frac_95 | B6 call distance | 0.873 [0.822, 0.945] | -0.030 [-0.048, -0.010] | +0.048 [+0.018, +0.074] |
| >=2 | time_frac_95 | B4 reverse-call reachability | 0.825 [0.754, 0.925] | -0.078 [-0.115, -0.032] | - |
| >=2 | time_frac_95 | B1 import-proximity | 0.842 [0.775, 0.934] | -0.061 [-0.096, -0.021] | +0.017 [+0.007, +0.027] |
| >=2 | time_frac_95 | B7 lexical overlap | 0.870 [0.817, 0.945] | -0.033 [-0.048, -0.014] | +0.045 [+0.013, +0.077] |

## Robustness of the >10 stratum result to clustering (ALL mutants, candidates = covering tests only)

Stratum >10: 113 killed mutants; distinct commits 7, distinct source files 51, distinct mutated functions 71.

| ranker | metric | cluster by | paired diff vs B5a [95% CI] | paired diff vs B4 [95% CI] |
|---|---|---|---|---|
| B4 reverse-call reachability | n95 | commit | -7.913 [-9.569, -5.972] | - |
| B4 reverse-call reachability | n95 | source file | -7.913 [-11.448, -4.766] | - |
| B4 reverse-call reachability | n95 | function | -7.913 [-11.331, -4.982] | - |
| B4 reverse-call reachability | recall@5 | commit | +0.195 [+0.169, +0.214] | - |
| B4 reverse-call reachability | recall@5 | source file | +0.195 [+0.114, +0.287] | - |
| B4 reverse-call reachability | recall@5 | function | +0.195 [+0.116, +0.279] | - |
| B4 reverse-call reachability | APFD | commit | +0.149 [+0.124, +0.171] | - |
| B4 reverse-call reachability | APFD | source file | +0.149 [+0.102, +0.195] | - |
| B4 reverse-call reachability | APFD | function | +0.149 [+0.104, +0.196] | - |
| B1 import-proximity | n95 | commit | -6.740 [-8.347, -4.681] | +1.173 [+0.837, +1.576] |
| B1 import-proximity | n95 | source file | -6.740 [-10.238, -3.823] | +1.173 [+0.546, +1.972] |
| B1 import-proximity | n95 | function | -6.740 [-10.209, -3.915] | +1.173 [+0.535, +2.006] |
| B1 import-proximity | recall@5 | commit | +0.119 [+0.101, +0.132] | -0.076 [-0.101, -0.050] |
| B1 import-proximity | recall@5 | source file | +0.119 [+0.057, +0.201] | -0.076 [-0.135, -0.029] |
| B1 import-proximity | recall@5 | function | +0.119 [+0.059, +0.197] | -0.076 [-0.132, -0.026] |
| B1 import-proximity | APFD | commit | +0.118 [+0.094, +0.138] | -0.031 [-0.044, -0.021] |
| B1 import-proximity | APFD | source file | +0.118 [+0.076, +0.163] | -0.031 [-0.053, -0.013] |
| B1 import-proximity | APFD | function | +0.118 [+0.079, +0.162] | -0.031 [-0.053, -0.012] |
| B5d coverage, broadest first | n95 | commit | -1.396 [-2.698, -0.242] | +6.517 [+3.908, +8.615] |
| B5d coverage, broadest first | n95 | source file | -1.396 [-4.626, +2.477] | +6.517 [+2.157, +12.888] |
| B5d coverage, broadest first | n95 | function | -1.396 [-4.431, +2.397] | +6.517 [+2.304, +12.978] |
| B5d coverage, broadest first | recall@5 | commit | +0.061 [+0.020, +0.098] | -0.135 [-0.175, -0.096] |
| B5d coverage, broadest first | recall@5 | source file | +0.061 [+0.024, +0.101] | -0.135 [-0.237, -0.044] |
| B5d coverage, broadest first | recall@5 | function | +0.061 [+0.025, +0.099] | -0.135 [-0.227, -0.052] |
| B5d coverage, broadest first | APFD | commit | +0.029 [+0.005, +0.055] | -0.120 [-0.157, -0.084] |
| B5d coverage, broadest first | APFD | source file | +0.029 [-0.024, +0.076] | -0.120 [-0.205, -0.049] |
| B5d coverage, broadest first | APFD | function | +0.029 [-0.021, +0.073] | -0.120 [-0.200, -0.053] |
| B6 call distance, ties broadest first | n95 | commit | -3.959 [-4.918, -2.846] | +3.954 [+1.880, +5.514] |
| B6 call distance, ties broadest first | n95 | source file | -3.959 [-7.310, +0.187] | +3.954 [+0.135, +10.397] |
| B6 call distance, ties broadest first | n95 | function | -3.959 [-7.158, -0.034] | +3.954 [+0.109, +10.280] |
| B6 call distance, ties broadest first | recall@5 | commit | +0.158 [+0.114, +0.191] | -0.037 [-0.061, -0.014] |
| B6 call distance, ties broadest first | recall@5 | source file | +0.158 [+0.089, +0.234] | -0.037 [-0.121, +0.023] |
| B6 call distance, ties broadest first | recall@5 | function | +0.158 [+0.093, +0.226] | -0.037 [-0.120, +0.020] |
| B6 call distance, ties broadest first | APFD | commit | +0.102 [+0.077, +0.123] | -0.047 [-0.066, -0.025] |
| B6 call distance, ties broadest first | APFD | source file | +0.102 [+0.039, +0.157] | -0.047 [-0.126, +0.004] |
| B6 call distance, ties broadest first | APFD | function | +0.102 [+0.044, +0.154] | -0.047 [-0.123, +0.005] |
| B5b coverage, most targeted first | n95 | commit | -0.786 [-1.709, +0.221] | +7.127 [+5.825, +8.000] |
| B5b coverage, most targeted first | n95 | source file | -0.786 [-4.036, +1.821] | +7.127 [+4.150, +10.670] |
| B5b coverage, most targeted first | n95 | function | -0.786 [-4.009, +1.683] | +7.127 [+4.275, +10.644] |
| B5b coverage, most targeted first | recall@5 | commit | +0.054 [+0.022, +0.083] | -0.141 [-0.170, -0.109] |
| B5b coverage, most targeted first | recall@5 | source file | +0.054 [-0.010, +0.142] | -0.141 [-0.205, -0.089] |
| B5b coverage, most targeted first | recall@5 | function | +0.054 [-0.006, +0.137] | -0.141 [-0.203, -0.085] |
| B5b coverage, most targeted first | APFD | commit | -0.012 [-0.039, +0.009] | -0.161 [-0.188, -0.132] |
| B5b coverage, most targeted first | APFD | source file | -0.012 [-0.059, +0.041] | -0.161 [-0.220, -0.106] |
| B5b coverage, most targeted first | APFD | function | -0.012 [-0.057, +0.039] | -0.161 [-0.218, -0.110] |
| B7 lexical overlap | n95 | commit | -3.460 [-4.055, -2.600] | +4.453 [+2.877, +5.758] |
| B7 lexical overlap | n95 | source file | -3.460 [-6.784, -0.925] | +4.453 [+2.499, +6.898] |
| B7 lexical overlap | n95 | function | -3.460 [-6.729, -0.989] | +4.453 [+2.584, +6.721] |
| B7 lexical overlap | recall@5 | commit | +0.110 [+0.086, +0.130] | -0.085 [-0.102, -0.065] |
| B7 lexical overlap | recall@5 | source file | +0.110 [+0.028, +0.203] | -0.085 [-0.136, -0.041] |
| B7 lexical overlap | recall@5 | function | +0.110 [+0.031, +0.199] | -0.085 [-0.134, -0.039] |
| B7 lexical overlap | APFD | commit | +0.067 [+0.055, +0.079] | -0.082 [-0.099, -0.066] |
| B7 lexical overlap | APFD | source file | +0.067 [+0.021, +0.115] | -0.082 [-0.123, -0.047] |
| B7 lexical overlap | APFD | function | +0.067 [+0.023, +0.115] | -0.082 [-0.121, -0.048] |
| ORACLE | n95 | commit | -19.281 [-20.768, -17.432] | -11.368 [-13.264, -9.486] |
| ORACLE | n95 | source file | -19.281 [-24.139, -14.664] | -11.368 [-14.824, -8.167] |
| ORACLE | n95 | function | -19.281 [-24.026, -14.690] | -11.368 [-14.542, -8.183] |
| ORACLE | recall@5 | commit | +0.414 [+0.375, +0.480] | +0.219 [+0.178, +0.294] |
| ORACLE | recall@5 | source file | +0.414 [+0.316, +0.505] | +0.219 [+0.149, +0.294] |
| ORACLE | recall@5 | function | +0.414 [+0.327, +0.501] | +0.219 [+0.159, +0.286] |
| ORACLE | APFD | commit | +0.284 [+0.259, +0.321] | +0.135 [+0.118, +0.165] |
| ORACLE | APFD | source file | +0.284 [+0.230, +0.332] | +0.135 [+0.101, +0.170] |
| ORACLE | APFD | function | +0.284 [+0.237, +0.328] | +0.135 [+0.105, +0.167] |
