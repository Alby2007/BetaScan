# P1 heuristic baselines — coverage prediction

C5 is a FIXED lexicographic formula `-10*impd - calld + 0.01*lex` — no fitting on labels (not in-sample).

| ranker | pooled AP | snap-macro AP | per-test AP | per-func AP | per-func AP (mutants) | P@R50 | P@R80 |
|---|---|---|---|---|---|---|---|
| C0 | 0.251 | 0.251 | 0.263 | 0.305 | 0.465 | 0.251 | 0.251 |
| C1 | 0.392 | 0.392 | 0.385 | 0.468 | 0.655 | 0.392 | 0.392 |
| C2 | 0.483 | 0.483 | 0.480 | 0.598 | 0.710 | 0.470 | 0.425 |
| C3 | 0.445 | 0.445 | 0.429 | 0.505 | 0.642 | 0.250 | 0.250 |
| C4 | 0.271 | 0.271 | 0.371 | 0.384 | 0.446 | 0.280 | 0.250 |
| C5 | 0.544 | 0.544 | 0.568 | 0.710 | 0.765 | 0.486 | 0.429 |

## era bands (snap-macro AP by snapshot positive rate)

| ranker | poslow n=4 |
|---|---|
| C0 | 0.251 |
| C1 | 0.392 |
| C2 | 0.483 |
| C3 | 0.445 |
| C4 | 0.271 |
| C5 | 0.544 |
