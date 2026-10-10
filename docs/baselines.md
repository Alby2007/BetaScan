# Baselines & metrics

All rankers see only the **parent commit P**: graph at P, coverage at P, history from earlier
parents. Candidates are either the full green suite or the covering set only (reported
separately — inside the covering set is the M4 question). Random tie-breaks average over 5 seeds.

## Rankers

| ID | Name | Definition |
|---|---|---|
| B0 | random | control |
| B1 | import-proximity | reverse-`imports` BFS distance from the changed file to each test file |
| B2 | history co-failure | per-file → per-dir → global co-failure rate, trained on earlier parents only |
| B3-A | LLM (diff) | unified diff of the change (±12 ctx) + covering test paths → JSON ranking |
| B3-B | LLM (diff+map) | A + each test's direct `src/` imports (does extra context help?) |
| B4 | reverse-call reachability | mutated fn (innermost containing the line) → reversed `calls` BFS; test rank = hops to any node in the test file; ties by import distance |
| B5a | coverage, random | covering tests first, random order — the reference coverage baseline |
| B5b | coverage, most targeted | covering tests, fewest total covered lines first (worse than B5a on h3) |
| B5c | coverage, historical | covering tests by historical failure rate |
| B5d | coverage, broadest | covering tests, most covered lines first (≈ B5a) |
| B6 | call distance, broadest | B4 distance, ties broadest-first (shows B4's import tie-break is the value) |
| B7 | lexical overlap | shared subtokens (camelCase-split, stoplist) between mutated entity (file path + function name) and test path |
| B8 | RRF(B3,B4) | reciprocal rank fusion (k=60), no learning — statistically ties B3-A |

B5 needs per-test coverage maps at P — its weakness operationally (maps go stale). The point of
B4/B3/B8 is whether comparable ranking is possible **without** fresh coverage.

## Metrics

| Metric | Meaning |
|---|---|
| `recall@k` / `hit@k` | fraction of failing tests found in top-k / any hit (k = 1,3,5 and 5/10/20% of candidates; only over mutants with > k covering tests) |
| `APFD` | average percentage of faults detected (ranking quality over the whole list) |
| `n95` | # tests needed to reach 95% of failing tests |
| `n95_vs_B5` | n95 ÷ covering-set size (< 1 beats plain "run everything that covers it") |
| `time_frac_95` | fraction of suite wall-time to reach 95% recall (needs `dur_ms`) |
| oracle | perfect ranking — headroom bound (`ceil(.95·failing)/covering`) |

Only **killed** mutants carry failing labels. Strata by covering-set size: `1`, `2-3`, `4-10`,
`>10` (+ `>=2` pool). On h3 only `>10` has oracle headroom (0.417 vs B5a 0.796); smaller strata
are saturated (oracle ≈ B5a ≈ run-almost-everything).

## Evaluation mechanics (`evaluate.py`)

- Rows: `rows_*.jsonl`; graphs: `graphs.db`; `covsize` from `--m2dir` records (`cov_P`).
- Temporal split (last `--test-parents` parents) + a "unseen file" strict view; **all-mutant**
  pooled tables for training-free rankers.
- Bootstrap: cluster-resample by `_p` (commit); robustness re-clustered by `_f` (src file) and
  `_fn` (file,function) — effective n ≈ #clusters, not #mutants.
- Emits: per-stratum tables (full-suite and covering-set candidates), failing-fraction/oracle
  table, paired-diff CI tables vs B5a and vs B4, the M4 go/no-go block (h3: GO — oracle 0.417 < 0.5
  and B5a 0.796 > 0.7), robustness table, and `OUT.md`.
- `--b3dir` points at the B3 output dir (default `data/b3`) — keep trpc B3 files in
  `data/trpc_b3/` so change_ids don't mix.
