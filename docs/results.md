
## Phase 2 corrections (post-review)

**Type-only filter bug (ours, not extractor)**: the (src,dst)-level type-only filter
over-excluded edges whose source also runtime-imports the same module. Fixed
statement-level (`impclass.py`). Post-fix: trpc covered-file closure ~98.3%;
residual 341 (t,f) pairs, ALL "type-only path" — files executed via `module:`
package edges (ts-morph resolved exports->dist, closed at closure level by mapping
module:X->in-repo package dir). C1 function-level on trpc: **precision 0.392,
recall 1.000** — the loss is over-prediction inside the closure, not missing edges.

**Expanded P1 metrics** (`data/covpred/p1_*.md`): snap-macro AP (equal snapshot
weight) C5 = 0.590 h3 / 0.544 trpc. Per-function ranking (the payoff task —
rank tests for a function) is much stronger: C5 = 0.835 h3 / 0.710 trpc,
0.846/0.765 on mutant-target functions. h3 era split: C5 = 0.797 (high-pos
snapshots) vs 0.399 (low-pos) — pooled AP mixes the eras. C5 is a FIXED
lexicographic formula `-10*impd - calld + 0.01*lex`; no fitting, not in-sample.

**Downstream preview** (h3, full suite, >10, fixed scores): C2 19.61 n95
(~B1 19.45 — parity), C5 18.77/0.965 vs **B4 17.97/0.929** — C5 does NOT beat
B4 downstream; B4 stays the bar. Forward call distance is near-dead on h3
(tests rarely call-reach mutants; 110/664 mutants have no function node anyway).

**Grouped-CV learnability check** (`data/covpred/cv_h3.md`, h3 dev repo,
HistGradientBoostingClassifier = documented LightGBM substitute, features from
the P3 spec, within-test percentile normalisation, fixed hyperparams,
exploratory): model beats C5 on every fold — pooled AP 0.613/0.848 vs 0.448/0.438
(grouped by source file / by test file, raw-path groups so no near-duplicate
snapshot leaks). Early attempt showed +0.5 AP from a `P:file` grouping leak —
fixed and documented. Result: coverage is learnable beyond heuristics -> P2
warranted. Single-repo CV does NOT establish cross-repo transfer (P3's job).
