# P0 — pairs table + label report

Empty-test baseline (stub `test("b",()=>{})` under each repo's own vitest config):
**h3 and trpc both cover ZERO src files** — setup helpers (e.g. `test/_setup.ts` on h3) are
imported per-test, not via vitest `setupFiles`, so no global-setup execution exists to subtract.
The baseline mask is empty here; it stays in the pipeline for P2 repos.

| repo | snapshots | tests (range) | functions in scope | pairs | pos rate | file-covered in import closure |
|---|---|---|---|---|---|---|
| h3 | 52 | 26–71 | 196–511 | 613131 | 0.231 | 0.80–0.95 (mean 0.880) |
| trpc | 4 | 98–100 | 854–1657 | 192940 | 0.250 | 0.81–0.83 (mean 0.820) |

Bimodality note (h3): snapshots with <=35 tests have pos rates ~0.60–0.71 vs ~0.11–0.13 for
larger suites — the covered-anywhere function universe shrinks with the suite, and h3's
app-level tests each cover a large fraction of src. Real, not a bug; matters for AP/imbalance.

Exclusions applied: baseline-covered files (none here), non-green tests (suite_P pass),
functions in test files, files never covered by any test (no executable evidence — caveat:
this also removes never-covered executable files, so negatives skew toward learnable ones).

One anomaly logged: trpc snapshot 6a70335e02 has 1657 function nodes vs ~855 on the other
three — different file-inclusion set in that graph; pairs still built from its own graph.
