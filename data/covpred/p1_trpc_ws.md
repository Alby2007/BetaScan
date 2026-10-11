# P1 heuristic baselines — coverage prediction

C5 is a FIXED lexicographic formula `-10*impd - calld + 0.01*lex` — no fitting on labels (not in-sample).

| ranker | pooled AP | snap-macro AP | per-test AP | per-func AP | per-func AP (mutants) | P@R50 | P@R80 |
|---|---|---|---|---|---|---|---|
| C0 | 0.251 | 0.251 | 0.263 | 0.305 | 0.462 | 0.251 | 0.251 |
| C1 | 0.392 | 0.392 | 0.387 | 0.471 | 0.649 | 0.392 | 0.392 |
| C2 | 0.483 | 0.483 | 0.481 | 0.598 | 0.706 | 0.470 | 0.426 |
| C3 | 0.445 | 0.445 | 0.429 | 0.505 | 0.644 | 0.250 | 0.250 |
| C4 | 0.271 | 0.271 | 0.371 | 0.384 | 0.444 | 0.280 | 0.250 |
| C5 | 0.545 | 0.545 | 0.569 | 0.711 | 0.763 | 0.486 | 0.430 |

## era bands (snap-macro AP by snapshot positive rate)

| ranker | poslow n=4 |
|---|---|
| C0 | 0.251 |
| C1 | 0.392 |
| C2 | 0.483 |
| C3 | 0.445 |
| C4 | 0.271 |
| C5 | 0.545 |
