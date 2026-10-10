# Pipeline

Five stages. Each stage script has a docstring with its exact CLI; this doc explains how they fit.

```
M0 suite runner ──> M2 labeller ──> rows.jsonl ──> M3 evaluator
                        ^                                 |
M1 extractor ──> graphs.db ───────────────────────────────┘
M4 scope probes (side quests: coverage-blind stratum, repo screen)
```

Everything a ranker or feature sees comes from the **parent commit P**: graph at P, coverage at
P, history from earlier parents only. No label leakage.

## M0 — suite runner (`stages/m0_runner/`)

`run_suite.py REPO [--commit SHA] [--out f.json] [--image impactnet-node] [--install CMD] [--test CMD]`

Archives the commit (`git archive`, never mutates the checkout), runs install + Vitest with the
JSON reporter inside the image, emits `{commit, wall_s, files: {path: {status, tests, failed,
duration_ms}}}`. Used by M2 for per-commit suite runs; also usable standalone for repo verification
(see `data/repo_verify/` for trpc/zod screens).

## M1 — static extractor (`stages/m1_extractor/`)

```bash
npm install                                        # once
node extract.mjs REPO [COMMIT] > graph.json        # ts-morph, repo tsconfig; no install needed
python build_db.py graph.json out.db               # -> SQLite nodes/edges, keyed by commit_hash
python queries.py out.db importers FILE | callers NAME | tests-importing FILE
```

Node kinds: `file`, `test_file`, `function` (functions, methods, ctors, accessors, fn-valued
consts), `class`, `type` (interfaces/aliases/enums), `module` (external pkgs).
Edge types: `imports`, `calls` (incl. `new`), `extends`, `implements`, `uses_type`, `defined_in`.
`covers` edges are added by M2 labelling, not the extractor.

Known gaps (by design): dynamic `import()` and calls through untyped/any values are unresolved;
overload signatures skipped; top-level calls attribute to the file node. Repos whose tsconfig
excludes test dirs yield 0 `test_file` nodes (extractor limitation — see `data/scope_repos.md`).

## M2 — labelling (`stages/m2_labeller/`)

h3 flow (per sampled parent P of a real commit C):

```bash
python harvest_commits.py REPO data/m2 --n 12 --seed 0 --skip-c   # suite runs at P (+C unless --skip-c)
python coverage_per_test.py REPO P out.json                       # per-test-file v8 coverage at P
python flake_log.py ...                                           # extra clean runs -> flake_log.json
python mutate_commits.py REPO data/m2 data/m2b_mut --min-cov 11 --per-commit 8
python build_mutant_dataset.py data/rows_clean.jsonl --pair data/m2:data/m2_mut --pair data/m2b:data/m2b_mut \
    --flake data/flake_log.json --flake data/flake_log_b.json
# (--worst-case variant counts unresolved mutants as all-covering-fail -> rows_worst.jsonl)
```

- **Mutants** are single-point ts-morph edits (`gen_mutants.mjs`): BinaryOp swaps
  (`===/!==`, `==/!=`, relational, `&&/||`, `??`→`&&`, `+`→`-`), Boolean true↔false,
  NegationRemoval, CondTrue/CondFalse, ReturnUndefined, StringEmpty, EmptyBody.
- **Run**: `run_mutants.mjs` inside the container splices one mutant at a time and runs **only the
  test files that cover the mutated line at P** (a non-executing test cannot observe it — audited,
  see `docs/caveats.md`). Each mutant runs twice; `Killed` requires failing in **both** runs.
- **Kill rule** (enforced at dataset build): a test counts as a killer only if green in every
  clean run AND failing in both mutant runs. Hangs (`Error`, secs ≥ 100) are retried file-by-file
  by `retry_timeouts.py` and mostly resolve as kills.
- **Green set** per parent = files passing all clean suite runs; non-green files are excluded
  from labels entirely.

`scale_h3.sh` orchestrated the 40-commit h3 scale-up (mutants only on lines covered by ≥11 green
tests — this is why the h3 `>10` stratum is populated but **not** population-representative).

trpc flow is a single end-to-end script — see `docs/trpc.md`.

## M3 — baselines + evaluator (`stages/m3_baselines/`)

```bash
python extract_graphs.py REPO MUTDIR data/graphs.db        # M1 extractor at every parent in the records
python evaluate.py data/rows_clean.jsonl data/graphs.db data/m3_eval --m2dir data/m2,data/m2b
python b3_llm.py ROWS.jsonl GRAPHS.db REPO data/b3 --variant A --provider gemini --model gemini-flash-lite-latest
python real_commit_strata.py ...                           # commits where coverage labels are undefined
python b3_b4_overlap.py                                    # B3/B4 complementarity analysis
```

Rankers and metrics: `docs/baselines.md`. The evaluator writes `OUT.md` with per-stratum tables,
clustered bootstrap CIs (commit, and as robustness also source-file and (file,function)), and the
pre-registered M4 go/no-go block.

## M4 — scoping probes (`stages/m4_scope/`)

- `scope_blind_files.py` — which non-`src/` files do tests reach through the graph (the
  coverage-blind stratum where B5 is undefined). h3: only ~5 informative files — too few.
- `scope_repos.py` — import-graph screen of candidate second repos (test-file counts, src-line
  coverage by >10 tests). Zod and trpc came out on top; trpc chosen.
