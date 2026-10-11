# B4 error analysis — what does the call graph not see?

Script: `stages/m3_baselines/b4_misses.py`. A "B4-miss" = a `>10`-stratum killed mutant where
B4's ranking puts at least half the failing tests in the bottom half of the covering set.

## trpc — 41/110 misses (37%)

| feature | miss | hit |
|---|---|---|
| failing tests not directly importing mutant file | 93.3% | 80.1% |
| failing tests in `packages/tests` integration suite | 95.7% | 85.4% |
| failing tests call-graph-unreachable | 42.6% | 37.3% |
| mean lexical overlap (mutant↔test tokens) | 1.80 | 2.74 |
| mutated-function reverse-call fan-in | 5.98 | 12.25 |
| mean failing tests per mutant | 24.5 | 10.9 |
| mean covering tests | 33.4 | 48.4 |

Mutators roughly uniform; misses concentrate in deep internals (TRPCUntypedClient,
getErrorShape, transformers, adapters).

## h3 — 112/280 misses (40%)

| feature | miss | hit |
|---|---|---|
| failing tests call-graph-unreachable | **79.5%** | 68.1% |
| failing tests not directly importing mutant file | 94.5% | 69.8% |
| mean lexical overlap | 0.14 | 0.59 |
| mutated-function fan-in | 1.98 | 1.32 |
| mean failing tests per mutant | 12.6 | 5.0 |

Misses concentrate in `src/response.ts` (29), `src/h3.ts` (19), `src/middleware.ts` (16) —
the framework core.

## Failing-fraction control (`--max-frac 0.5`, nfail/ncov < 0.5)

The uncontrolled miss table is confounded: B4 misses carry ~2.2x more failing tests, so
any property of "the failing tests" partly reflects having more of them. Restricting to
mutants with failing fraction < 0.5:

trpc — 108 mutants, 24 misses (22%) vs 84 hits:

| feature | miss | hit |
|---|---|---|
| frac failing tests call-unreachable | 0.589 | 0.462 |
| frac failing tests integration-suite | 1.000 | 0.825 |
| frac failing tests directly importing | 0.074 | 0.179 |
| mean lexical overlap | 1.60 | 3.04 |
| fan-in of mutated fn | 2.96 | 10.37 |
| mocks | 0.70 | 0.66 |
| mean failing tests (confound removed) | 3.29 | 5.66 |

h3 — 179 mutants, 34 misses (19%) vs 145 hits:

| feature | miss | hit |
|---|---|---|
| frac failing tests call-unreachable | 0.825 | 0.676 |
| frac failing tests directly importing | 0.052 | 0.337 |
| mean lexical overlap | 0.244 | 0.659 |
| fan-in | 1.21 | 1.25 |
| mocks | 0.31 | 0.26 |
| dynamic import() | 0.00 | 0.05 |

Directions survive the control on both repos — so the profile below is a *supported
hypothesis*, not a failing-fraction artefact. But note the second problem the reviewer
raised: on h3 even B4's HITS have 68% of failing tests call-unreachable, so the call
layer's contribution must be measured directly, which the ablation below does.

## B4 edge-type ablation (the actual decomposition)

B4 = reverse-`calls` BFS distance, ties broken by import distance. `B4c` = calls only
(ties by name). `B1` = import distance only. `>10` stratum, commit-clustered paired
diffs vs B5a (and vs B4):

| repo | ranker | n95 | vs B5a | r@5 | APFD | vs B4 n95 |
|---|---|---|---|---|---|---|
| h3 | B4 combined | 12.71 | -4.34 | 0.497 | 0.649 | - |
| h3 | B1 imports-only | 13.83 | -3.22 (74% of gain) | 0.420 | 0.609 | +1.12 [+0.57,+1.79] |
| h3 | B4c calls-only | 15.25 | -1.80 (42%) | 0.379 | 0.569 | +2.54 [+1.51,+3.60] |
| trpc | B4 combined | 28.88 | -6.39 | 0.311 | 0.624 | - |
| trpc | B1 imports-only | 29.77 | -5.50 (86% of gain) | 0.243 | 0.596 | +0.89 [+0.40,+1.55] |
| trpc | B4c calls-only | 33.02 | -2.25 (35%) | 0.247 | 0.555 | +4.14 [+2.92,+5.24] |

On BOTH repos **import distance carries most of B4**; call edges add a real but modest
increment over imports alone (~+1 n95 unit, CIs exclude 0), while calls alone is barely
better than random. B4 is substantially an import-proximity heuristic with a thin call
layer on top — which reframes the miss analysis: the residual gap to oracle lives where
NEITHER signal exists, not where call edges fail alone.

## Unified pattern (both repos) — hypothesis, not established

B4 misses are mutants in code reached through a **registration/indirection layer** that
yields no `calls` edge: h3's `defineEventHandler`/`app.use` handler table and middleware
pipeline; trpc's `initTRPC` link-array composition and `createCaller` factories. The known
extractor gap (calls through untyped/any receivers unresolved) is exactly where these live.
The failing-fraction control above keeps the pattern visible, but this remains
hypothesis-supporting evidence — the decisive test would be a ranker that actually
implements a registration edge.

Consistent secondary signals, both repos:

- failing tests almost never directly import the mutant file (5–7% vs 20–30% for hits)
- failing tests share few name tokens with the mutant (lexical gap → why B7 also weakens)
- misses have *more* failing tests per mutant (~2.2×) — broad blast radius; the surviving
  ~30–40% is what needs ordering, and those survivors exercise the file via an unrelated
  path (different link/adapter/route). Call-graph distance cannot separate
  "covers but doesn't depend on the mutated path" from "covers and does".
- mocks and dynamic `import()` are NOT the discriminating factor (similar rates in both
  classes on both repos).

## Candidate structure encodings (post-M1, not features yet)

1. **Registration edges**: "module X registers handler/link under name Y" — pairs with
   "test references Y". Captures the dispatch-table indirection both repos use.
2. **Path-aware weighting** instead of flat BFS distance: weight edges by how much of the
   caller's surface goes through the callee, so the 30%-survivor separation is possible.
3. **Mock-aware edges** probably low-yield: mock usage is high everywhere and does not
   discriminate misses from hits on either repo.
