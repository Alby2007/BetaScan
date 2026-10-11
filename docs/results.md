# Results

## h3 — complete

52 parents, 664 usable mutants (488 killed, 176 survived, 1 unresolved; unresolved counted both
ways — verdict unchanged). `>10`-stratum n=280 killed mutants from 51 commits, 39 source files,
89 mutated functions (effective n ≈ clusters, not 280).

Pre-registered go/no-go (`>10`, commit-clustered): oracle n95/ncov 0.417 [0.354, 0.484] < 0.5 and
B5a 0.796 [0.768, 0.825] > 0.7 → **GO**. Other strata have no headroom (oracle ≥ 0.83).

### Covering-set ranking, `>10` stratum (n=280)

| Ranker | n95 | recall@5 | APFD |
|---|---|---|---|
| ORACLE | 7.90 | 0.746 | 0.789 |
| B8 RRF(B3,B4) — free | 11.84 | 0.554 | 0.683 |
| B3-A LLM (gemini-flash-lite) | 11.89 | 0.556 | 0.682 |
| B4 reverse call-graph — free, deterministic | 12.71 | 0.497 | 0.649 |
| B7 lexical overlap | 14.74 | 0.426 | 0.594 |
| B5a coverage-random | 17.05 | 0.264 | 0.501 |

Key comparisons (commit-clustered paired diffs; same direction under file/function clustering):

- **B8 vs B4**: n95 −0.87, recall@5 +0.056, APFD +0.034 — fusion significantly beats B4.
- **B8 vs B3-A**: n95 −0.05, recall@5 −0.002, APFD +0.0004 — **statistical tie** on every metric.
  B3 already contains what B4 adds; uniform fusion captures nothing extra.
- **B3-A vs B4**: n95 −0.82 (tie), recall@5 +0.059, APFD +0.034 — LLM narrowly ahead; it reads
  most of the structure signal from names + diff alone.
- B7 << B4 — the LLM's edge is semantic, not string matching (B7 recovers ~40% of the B5a→oracle
  recall@5 gap, B4 ~57%, B3-A ~71%).
- B3/B4 complementarity was **corrected**: union-of-top-5s is a budget artifact; best-top-10 wins.

**M1 bar (pre-registered):** beat best of B3/B4/B7/B8 → effectively B3-A ≈ B8
(n95 ~11.8, recall@5 ~0.556, APFD ~0.682). B4 stays reported separately (free, instant,
deterministic — vs B3's per-change API cost).

B3 details: `gemini-flash-lite-latest` (served `gemini-3.5-flash-lite`), temp 0, 380 calls, 0 parse
failures; prompt verbatim in `data/b3/SYSTEM_PROMPT.txt`, raw responses logged.

Full tables incl. all clusterings: `data/m3_b3.md`.

## trpc — held-out results (clean dataset, `>10` stratum)

Pilot complete: 7 commits, 141 mutants, 110 killed, 58 distinct src files. Go/no-go **GO**
(oracle n95/ncov 0.430, B5a 0.846; worst-case unchanged). Baselines inside the covering set:

| Ranker | n95 | recall@5 | APFD |
|---|---|---|---|
| ORACLE | 15.47 | 0.565 | 0.779 |
| B4 reverse-call — free | 27.15 | 0.340 | 0.641 |
| B8 RRF(B3,B4) — free | 27.75 | 0.347 | 0.644 |
| B1 import | 28.36 | 0.261 | 0.609 |
| B3-A LLM (same model+prompt as h3) | 29.83 | 0.351 | 0.627 |
| B7 lexical | 31.73 | 0.252 | 0.556 |
| B5a coverage-random | 35.28 | 0.139 | 0.488 |

(B3-A/B8 cover 99/110 mutants — the 11 dropped are non-regenerating old-config mutants; see
`docs/caveats.md`.)

- **B4 vs B5a**: n95 −8.13, recall@5 +0.201, APFD +0.153 — survives source-file and function
  clustering (n95 file [−11.70, −4.96]); 7 commits is too few to cluster on, 50 files is the unit.
- **Ordering flips vs h3**: there B3-A ≈ B8 > B4; on trpc B4 ≈ B8 and B3-A shows **no
  detectable difference** from B4 — directionally worse on n95 but the file-clustered CI
  includes 0 (+1.96 [−0.15, +4.24] on the 117 common set; the commit-clustered CI excludes 0;
  ties on recall@5/APFD). The structural heuristic is the cross-repo stable ranker; the
  diff-reading LLM is not. trpc contamination risk applies to B3's favour, so this is
  conservative evidence for structure.
- **Gap-closed share by B4** (random→oracle): trpc ~33% n95 / ~39% recall@5 / ~45% APFD;
  h3 ~half — i.e. "a third to a half", not "about half" on both.
- **B4 decomposition** (edge-type ablation, `data/b4_misses.md`): import proximity (B1)
  delivers ~74% (h3) / ~86% (trpc) of B4's n95 gain; call edges add ~+1 n95 unit, significant
  but small — the working signal is mostly **coarse module distance**, not deep program
  reasoning, consistent with the miss analysis (failing tests rarely import the mutant file).

## M1 — trained on h3, frozen before trpc scoring

sklearn HistGradientBoostingClassifier (max_iter 150, lr 0.05, leaves 15, L2 1.0), 12
repo-agnostic features, GroupKFold(5) by src_file — spec: `data/m1/m1_spec.json`.

h3 grouped-CV sanity (`>10`, n=280): no-B3 variant n95 12.59 / r@5 0.494 / APFD 0.641 (≈B4);
+B3-stack 11.62 / 0.533 / 0.663 (below B3-A). Consistent with "no complementary signal to
harvest". Pre-registered trpc tiers: **WIN** paired n95 CI excludes 0 in M1's favour; **MATCH**
within ±10% of best-of-B3-A/B8 n95 (zero inference cost); **LOSS** otherwise → ship B4.

## M1 on trpc — scored once, frozen set

`data/trpc_eval_m1.md`. PRIMARY (M1 vs B4, all 184, file-clustered): n95 29.95 vs 28.88,
paired +1.07 [−0.74, +2.93] → **INCONCLUSIVE** (point +3.7% inside ±2.89 margin, CI not
entirely within; commit clustering would read LOSS). recall@5/APFD directionally worse.
SECONDARY (117 common set, bar B8): **LOSS** for both M1 (+2.31) and the B3-stack (+1.44).
M1 ≈ B3-A on n95 (tie) but worse on recall@5/APFD. Consistent with the pre-registered
covariate-shift caveat: top features `log_ncov`/`targeted_lines` shifted out of their h3
ranges. Conclusion: ship the heuristic (B4, or B8 where B3 rankings exist).

## What has NOT been measured yet

- Reverse direction (train trpc → test h3) — secondary check
- B3 addendum on the remaining 56 quota-blocked mutants (cannot change the primary verdict)
- Stronger-model B3 rerun on trpc (prompts now persisted; explicit versioned model name)
- Real-commit stratum (coverage undefined: config/fixtures) — h3 has 3/12 commits, 0 labels; too thin

## Phase 2 � coverage prediction from static structure

P0 labels (`data/covpred/`): empty-test baseline covers **zero** src files on both repos
(setup helpers are per-test imports, not vitest `setupFiles`) � nothing to subtract;
mask kept for P2 repos. Pairs: h3 613k (52 snapshots, pos 0.23 pooled � bimodal
0.11�0.13 on ~45�71-test snapshots vs 0.60�0.71 on ~26�35-test ones), trpc 193k
(4 snapshots, pos 0.25). Runtime import closure explains ~89% (h3) / ~82% (trpc)
of covered *files*.

P1 heuristics, function-level AP (`data/covpred/p1_*.md`):

| ranker | h3 pooled | h3 per-test | trpc pooled | trpc per-test |
|---|---|---|---|---|
| C0 random | 0.231 | 0.303 | 0.251 | 0.263 |
| C1 imp closure | 0.338 | 0.463 | 0.369 | 0.356 |
| C2 imp distance | 0.379 | 0.520 | 0.469 | 0.484 |
| C3 call reach | 0.348 | 0.538 | 0.445 | 0.429 |
| C4 lexical | 0.271 | 0.409 | 0.271 | 0.371 |
| C5 (impd, calld, lex) | 0.431 | 0.606 | 0.533 | 0.571 |

Headroom gate: NOT triggered (C5 < 0.9 on both). Import *distance ordering* beats
binary closure � granularity carries signal; call reach is sparse (P@R>=50 collapses
to base rate). Learner target: beat C5 on held-out repos.
