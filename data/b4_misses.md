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

## Unified pattern (both repos)

B4 misses are mutants in code reached through a **registration/indirection layer** that
yields no `calls` edge: h3's `defineEventHandler`/`app.use` handler table and middleware
pipeline; trpc's `initTRPC` link-array composition and `createCaller` factories. The known
extractor gap (calls through untyped/any receivers unresolved) is exactly where these live.

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
